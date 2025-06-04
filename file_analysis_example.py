import os

from dotenv import load_dotenv

from src.agent_core import AgentType, MultiAgentCodingAI


def analyze_file(file_path: str, request: str):
    """
    Analyze a file using the appropriate agent based on file type and request.

    Args:
        file_path (str): Path to the file to analyze
        request (str): The analysis request or question about the file
    """
    try:
        # Initialize the multi-agent system
        agent_system = MultiAgentCodingAI()

        # Determine which agent to use based on the request
        agent_type = None
        if any(word in request.lower() for word in ["analyze", "data", "insights", "report", "chart"]):
            agent_type = AgentType.DATA_ANALYSIS
        elif any(word in request.lower() for word in ["automate", "workflow", "process"]):
            agent_type = AgentType.AUTOMATION
        elif any(word in request.lower() for word in ["create", "write", "content"]):
            agent_type = AgentType.CONTENT_CREATION
        else:
            # Default to data analysis for file analysis
            agent_type = AgentType.DATA_ANALYSIS

        # Get the appropriate agent
        agent = agent_system.agents[agent_type]

        # Process the file
        print(f"\nProcessing file: {file_path}")
        with open(file_path, "rb") as f:
            file_data = agent.process_file(file=f, filename=os.path.basename(file_path))

        # Process the request with the file
        print(f"\nAnalyzing with request: {request}")
        response = agent.process_request(request=request, files=[file_data])

        # Print the results
        print("\n=== Analysis Results ===")
        print(response.content)

        if response.data and "processed_files" in response.data:
            print("\n=== File Information ===")
            for file_info in response.data["processed_files"]:
                print(f"\nFile: {file_info['filename']}")
                print(f"Type: {file_info['type']}")
                print(f"Size: {file_info['size']} bytes")
                if file_info["metadata"]:
                    print("Metadata:")
                    for key, value in file_info["metadata"].items():
                        print(f"  {key}: {value}")

        # Cleanup
        agent.cleanup_files()

    except Exception as e:
        print(f"Error during file analysis: {str(e)}")


def main():
    # Load environment variables
    load_dotenv()

    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not found in environment variables")
        return

    while True:
        print("\n=== File Analysis System ===")
        print("1. Analyze a file")
        print("2. Exit")

        choice = input("\nEnter your choice (1-2): ").strip()

        if choice == "2":
            break
        elif choice == "1":
            file_path = input("\nEnter the path to your file: ").strip()
            if not os.path.exists(file_path):
                print(f"Error: File not found at {file_path}")
                continue

            print("\nWhat would you like to do with the file?")
            print("Examples:")
            print("- Analyze this data and provide insights")
            print("- Create a workflow to automate processing this file")
            print("- Generate a report from this data")
            print("- Extract key information from this document")

            request = input("\nEnter your request: ").strip()

            analyze_file(file_path, request)
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
