import json

# Your Firebase JSON file path
json_file_path = r"C:\Users\shitt\Downloads\multiagentai21-9a8fc-firebase-adminsdk-fbsvc-72f0130c73.json"

try:
    # Read the JSON file
    with open(json_file_path, 'r') as file:
        firebase_config = json.load(file)
    
    # Convert to single-line JSON string
    env_var_value = json.dumps(firebase_config, separators=(',', ':'))
    
    print("🔥 SUCCESS! Here's your FIREBASE_CREDENTIALS environment variable:")
    print("=" * 100)
    print(env_var_value)
    print("=" * 100)
    
    print("\n📋 COPY THE ABOVE STRING and use it as your FIREBASE_CREDENTIALS environment variable")
    
    print(f"\n✅ Validation:")
    print(f"   Project ID: {firebase_config.get('project_id')}")
    print(f"   Client Email: {firebase_config.get('client_email')}")
    print(f"   Type: {firebase_config.get('type')}")
    
    # Save to clipboard if pyperclip is available
    try:
        import pyperclip
        pyperclip.copy(env_var_value)
        print("\n📋 Copied to clipboard!")
    except ImportError:
        print("\n💡 Tip: Install pyperclip to auto-copy to clipboard: pip install pyperclip")
    
    # Save to .env file
    with open('.env.firebase', 'w') as env_file:
        env_file.write(f'FIREBASE_CREDENTIALS={env_var_value}\n')
    print("💾 Saved to .env.firebase file")
    
except FileNotFoundError:
    print("❌ File not found! Make sure the path is correct:")
    print(f"   {json_file_path}")
except Exception as e:
    print(f"❌ Error: {e}")