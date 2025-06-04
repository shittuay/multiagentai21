import os
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from src.agent_core import MultiAgentCodingAI, AgentType
from dotenv import load_dotenv
import threading

class FileUploadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Analysis Uploader")
        self.root.geometry("800x600")
        
        # Initialize agent system
        self.agent_system = None
        self.initialize_agent()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File selection
        ttk.Label(self.main_frame, text="Select File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.file_path_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.main_frame, text="Browse", command=self.browse_file).grid(row=0, column=2)
        
        # Analysis type selection
        ttk.Label(self.main_frame, text="Analysis Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.analysis_type = tk.StringVar(value="data")
        ttk.Radiobutton(self.main_frame, text="Data Analysis", variable=self.analysis_type, 
                       value="data").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(self.main_frame, text="Image Analysis", variable=self.analysis_type, 
                       value="image").grid(row=1, column=1, sticky=tk.E)
        
        # Request input
        ttk.Label(self.main_frame, text="Analysis Request:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.request_text = scrolledtext.ScrolledText(self.main_frame, width=60, height=4)
        self.request_text.grid(row=2, column=1, columnspan=2, pady=5)
        self.request_text.insert(tk.END, "Analyze this data and provide insights")
        
        # Status and results
        ttk.Label(self.main_frame, text="Status:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.main_frame, textvariable=self.status_var).grid(row=3, column=1, sticky=tk.W)
        
        ttk.Label(self.main_frame, text="Results:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.results_text = scrolledtext.ScrolledText(self.main_frame, width=60, height=15)
        self.results_text.grid(row=4, column=1, columnspan=2, pady=5)
        
        # Upload button
        self.upload_button = ttk.Button(self.main_frame, text="Analyze File", command=self.analyze_file)
        self.upload_button.grid(row=5, column=1, pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.main_frame, length=300, mode='indeterminate')
        self.progress.grid(row=6, column=1, pady=5)
        
        # Configure grid weights
        self.main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def initialize_agent(self):
        """Initialize the agent system"""
        try:
            load_dotenv()
            if not os.getenv('GEMINI_API_KEY'):
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            self.agent_system = MultiAgentCodingAI()
            print("Agent system initialized successfully")
        except Exception as e:
            print(f"Error initializing agent system: {e}")
            self.show_error("Failed to initialize agent system. Please check your API key.")
    
    def browse_file(self):
        """Open file dialog to select a file"""
        filetypes = [
            ('All Files', '*.*'),
            ('CSV Files', '*.csv'),
            ('Excel Files', '*.xlsx;*.xls'),
            ('Text Files', '*.txt'),
            ('Image Files', '*.png;*.jpg;*.jpeg;*.gif'),
            ('PDF Files', '*.pdf')
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.file_path_var.set(filename)
            # Update default request based on file type
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.analysis_type.set("image")
                self.request_text.delete(1.0, tk.END)
                self.request_text.insert(tk.END, "Analyze this image and describe its contents")
            else:
                self.analysis_type.set("data")
                self.request_text.delete(1.0, tk.END)
                self.request_text.insert(tk.END, "Analyze this data and provide insights")
    
    def analyze_file(self):
        """Analyze the selected file"""
        if not self.agent_system:
            self.show_error("Agent system not initialized")
            return
        
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            self.show_error("Please select a valid file")
            return
        
        request = self.request_text.get(1.0, tk.END).strip()
        if not request:
            self.show_error("Please enter an analysis request")
            return
        
        # Start analysis in a separate thread
        self.upload_button.state(['disabled'])
        self.progress.start()
        self.status_var.set("Analyzing...")
        self.results_text.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self._run_analysis, args=(file_path, request))
        thread.daemon = True
        thread.start()
    
    def _run_analysis(self, file_path: str, request: str):
        """Run the analysis in a background thread"""
        try:
            # Determine agent type
            agent_type = AgentType.DATA_ANALYSIS
            if self.analysis_type.get() == "image":
                agent_type = AgentType.CONTENT_CREATION
            
            agent = self.agent_system.agents[agent_type]
            
            # Process the file
            with open(file_path, 'rb') as f:
                file_data = agent.process_file(
                    file=f,
                    filename=os.path.basename(file_path)
                )
            
            # Process the request
            response = agent.process_request(
                request=request,
                files=[file_data]
            )
            
            # Update UI with results
            self.root.after(0, self._update_results, response)
            
        except Exception as e:
            self.root.after(0, self.show_error, f"Error during analysis: {str(e)}")
        finally:
            self.root.after(0, self._analysis_complete)
    
    def _update_results(self, response):
        """Update the results text with the analysis response"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== Analysis Results ===\n\n")
        self.results_text.insert(tk.END, response.content)
        
        if response.data and 'processed_files' in response.data:
            self.results_text.insert(tk.END, "\n\n=== File Information ===\n")
            for file_info in response.data['processed_files']:
                self.results_text.insert(tk.END, f"\nFile: {file_info['filename']}\n")
                self.results_text.insert(tk.END, f"Type: {file_info['type']}\n")
                self.results_text.insert(tk.END, f"Size: {file_info['size']} bytes\n")
                if file_info['metadata']:
                    self.results_text.insert(tk.END, "Metadata:\n")
                    for key, value in file_info['metadata'].items():
                        self.results_text.insert(tk.END, f"  {key}: {value}\n")
    
    def _analysis_complete(self):
        """Clean up after analysis is complete"""
        self.progress.stop()
        self.upload_button.state(['!disabled'])
        self.status_var.set("Analysis Complete")
    
    def show_error(self, message: str):
        """Show error message"""
        self.status_var.set("Error")
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Error: {message}")
        self.progress.stop()
        self.upload_button.state(['!disabled'])

def main():
    root = tk.Tk()
    app = FileUploadApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 