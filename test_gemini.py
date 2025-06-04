import os

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_gemini():
    try:
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            return

        print(f"🔑 Using API key: {api_key[:8]}...")

        # Configure
        genai.configure(api_key=api_key)

        # Try specific stable models first
        stable_models = [
            "models/gemini-1.5-pro-002",  # Latest stable Pro model
            "models/gemini-1.5-flash-002",  # Latest stable Flash model
            "models/gemini-1.5-flash-8b-001",  # Latest stable Flash-8B model
        ]

        for model_name in stable_models:
            try:
                print(f"\n🔄 Trying stable model: {model_name}")
                model_instance = genai.GenerativeModel(model_name)
                print(f"✅ Model initialized: {model_name}")

                # Try a simple prompt
                response = model_instance.generate_content("Say hello!")
                if response and hasattr(response, "text"):
                    print(f"✅ Test response: {response.text}")
                    return
                else:
                    print(f"❌ No text in response from {model_name}")
                    continue

            except Exception as e:
                print(f"❌ Error with model {model_name}: {e}")
                continue

        # If stable models fail, list and try all available models
        print("\n📋 Listing available models:")
        try:
            models = genai.list_models()
            for model in models:
                if "generateContent" in model.supported_generation_methods:
                    print(f"\n🔄 Trying model: {model.name}")
                    print(f"Model details:")
                    print(f"  Display name: {model.display_name}")
                    print(f"  Description: {model.description}")
                    print(f"  Generation methods: {model.supported_generation_methods}")

                    try:
                        model_instance = genai.GenerativeModel(model.name)
                        print(f"✅ Model initialized: {model.name}")

                        # Try a simple prompt
                        response = model_instance.generate_content("Say hello!")
                        if response and hasattr(response, "text"):
                            print(f"✅ Test response: {response.text}")
                            return
                        else:
                            print(f"❌ No text in response from {model.name}")
                            continue

                    except Exception as e:
                        print(f"❌ Error with model {model.name}: {e}")
                        continue

            print("❌ No working models found that support generateContent")

        except Exception as e:
            print(f"❌ Error listing models: {e}")
            return

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_gemini_response():
    """Test basic Gemini API response."""
    response = get_gemini_response("Hello, how are you?")
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0


def test_gemini_error_handling():
    """Test error handling in Gemini API calls."""
    # Test with invalid API key
    original_key = os.getenv("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = "invalid_key"
    try:
        response = get_gemini_response("test")
        assert response is None
    finally:
        os.environ["GEMINI_API_KEY"] = original_key


if __name__ == "__main__":
    test_gemini_response()
    test_gemini_error_handling()
    print("All tests passed!")
