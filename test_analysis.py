import json
import os
import traceback
import webbrowser

from src.data_analysis import DataAnalyzer


def test_analysis():
    # Initialize the analyzer
    analyzer = DataAnalyzer()

    try:
        # Verify file exists
        if not os.path.exists("employee_data.csv"):
            print("Error: employee_data.csv not found in current directory")
            return

        print("\nAnalyzing employee data...")
        print("Current working directory:", os.getcwd())
        print("File exists:", os.path.exists("employee_data.csv"))

        # Test employee data analysis
        results = analyzer.analyze_file("employee_data.csv")

        # Debug print
        print("\nRaw results:", json.dumps(results, indent=2))

        if isinstance(results, dict) and "error" in results:
            print("\nAnalysis Error:", results["error"])
            if "traceback" in results:
                print("Traceback:", results["traceback"])
            return

        # Print summary of results
        if "summary" in results:
            print("\nAnalysis Summary:")
            print(f"Total records: {results['summary']['total_records']}")
            print(f"Columns analyzed: {', '.join(results['summary']['columns'])}")
        else:
            print("\nWarning: No summary found in results")
            print("Available keys:", list(results.keys()))

        # Print recommendations if any
        if "recommendations" in results:
            print("\nRecommendations:")
            for rec in results["recommendations"]:
                print(f"- {rec}")

        # Open interactive visualizations
        if "visualizations" in results:
            print("\nOpening visualizations in browser...")
            for viz_type, path in results["visualizations"].items():
                if "interactive" in viz_type:
                    print(f"Opening {viz_type}...")
                    webbrowser.open(path)

        # Save detailed results to a JSON file
        with open("analysis_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\nDetailed results saved to 'analysis_results.json'")

    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
    finally:
        # Clean up temporary files
        analyzer.cleanup()


if __name__ == "__main__":
    test_analysis()
