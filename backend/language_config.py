LANGUAGE_CONFIG = {
    "cpp": {
        "filename": "main.cpp",
        "compile": ["g++", "main.cpp", "-o", "main"],
        "run": ["./main"],
    },
    "python": {
        "filename": "main.py",
        "compile": None,
        "run": ["python3", "main.py"],
    },
    "java": {
        "filename": "Main.java",
        "compile": ["javac", "Main.java"],
        "run": ["java", "Main"],
    },
    "javascript": {
        "filename": "main.js",
        "compile": None,
        "run": ["node", "main.js"],
    },
}