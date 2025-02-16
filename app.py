#app.py
# /// script
# requires-python = ">=3.13" 
# dependencies = [
#   "requests",
#   "fastapi",
#   "uvicorn",
#   "python-dateutil",
#   "pandas",
#   "db-sqlite3",
#   "scipy",
#   "pybase64",
#   "python-dotenv",
#   "httpx",
#   "markdown",
#   "duckdb",
#   "pillow",
#   "beautifulsoup4",
#   "whisper",
#   "json5",
#   "pathlib"
# ]
# ///


from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from tasksA import *
from tasksB import *
import requests
from dotenv import load_dotenv
import os
import re
import httpx
import json



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


app = FastAPI()
load_dotenv()

# @app.get('/ask')
# def ask(prompt: str):
#     """ Prompt Gemini to generate a response based on the given prompt. """
#     gemini_api_key = os.getenv('gemini_api_key')
#     if not gemini_api_key:
#         return JSONResponse(content={"error": "GEMINI_API_KEY not set"}, status_code=500)

#     # Read the contents of tasks.py
#     with open('tasks.py', 'r') as file:
#         tasks_content = file.read()

#     # Prepare the request data
#     data = {
#         "contents": [{
#             "parts": [
#                 {"text": f"Find the task function from here for the below prompt:\n{tasks_content}\n\nPrompt: {prompt}\n\n respond with the function_name and function_parameters with parameters in json format"},
#             ]
#         }]
#     }

#     url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
#     headers = {
#         "Content-Type": "application/json"
#     }

#     response = requests.post(url, json=data, headers=headers)

#     if response.status_code == 200:
#         text_reponse = response.json()["candidates"][0]["content"]["parts"][0]["text"]
#         match = re.search(r'```json\n(.*?)\n```', text_reponse, re.DOTALL)
#         text_reponse = match.group(1).strip() if match else text_reponse
#         return json.loads(text_reponse)
#         # return JSONResponse(content=response.json(), status_code=200)
#     else:
#         return JSONResponse(content={"error": "Failed to get response", "details": response.text}, status_code=response.status_code)

@app.get("/ask")
def ask(prompt: str):
    result = get_completions(prompt)
    return result

openai_api_chat  = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions" # for testing
openai_api_key = os.getenv("AIPROXY_TOKEN")

headers = {
    "Authorization": f"Bearer {openai_api_key}",
    "Content-Type": "application/json",
}

function_definitions_llm = [
   {
        "name": "A1",
        "description": "Install 'uv' (if not already installed) and run a Python script from a specified URL, passing the user's email as an argument. This script generates data files required for subsequent tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "script_url": {
                    "type": "string",
                    "pattern": "https?://.*\\.py",
                    "description": "The URL of the Python script to be executed."
                },
                "email": {
                    "type": "string",
                    "pattern": "[\\w\\.-]+@[\\w\\.-]+\\.\\w+",
                    "description": "The email address to be passed as an argument to the script."
                }
            },
            "required": ["script_url", "email"]
        }
    },
    {
        "name": "A2",
        "description": "Format a markdown file using a specified version of Prettier.",
        "parameters": {
            "type": "object",
            "properties": {
                "prettier_version": {"type": "string", "pattern": r"prettier@\d+\.\d+\.\d+"},
                "filename": {"type": "string", "pattern": r".*/(.*\.md)"}
            },
            "required": ["prettier_version", "filename"]
        }
    },
    {
        "name": "A3",
        "description": "Count the number of occurrences of a specific weekday in a date file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/data/.*dates.*\.txt"},
                "targetfile": {"type": "string", "pattern": r"/data/.*/(.*\.txt)"},
                "weekday": {"type": "integer", "pattern": r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"}
            },
            "required": ["filename", "targetfile", "weekday"]
        }
    },
    {
        "name": "A4",
        "description": "Sort a JSON contacts file and save the sorted version to a target file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.json)",
                },
                "targetfile": {
                    "type": "string",
                    "pattern": r".*/(.*\.json)",
                }
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "B6",
        "description": "Extract data from a website and save it as JSON or CSV.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "pattern": "^(https?:\\/\\/)(?!localhost|127\\.0\\.0\\.1|internal).*",
                    "description": "Publicly accessible URL to scrape (must not be local/internal)."
                },
                "data_type": {
                    "type": "string",
                    "enum": ["text", "links", "tables"],
                    "description": "Type of data to extract: plain text, links, or tables."
                },
                "output_filename": {
                    "type": "string",
                    "pattern": "^/data/.*\\.(json|csv)$",
                    "description": "Path to save scraped data (must be inside /data/)."
                }
            },
            "required": ["url", "data_type", "output_filename"]
        }
    },
    {
        "name": "A7",
        "description": "Extract the sender's email address from a text file and save it to an output file. Ensure that the correct argument names are used exactly as specified: 'filename' and 'output_file'. Do NOT alter the argument names (e.g., do NOT use 'output file' instead of 'output_file').",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "default": "/data/email.txt"
                },
                "output_file": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "default": "/data/email-sender.txt"
                }
            },
            "required": ["filename", "output_file"]
        }
    },

    {
        "name": "A8",
        "description": "Extract the financial card number from an image file using an LLM and save it as plain text without spaces.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "pattern": ".*/(.*\\.txt)",
                    "default": "/data/credit-card.txt",
                    "description": "Path to the output text file where the extracted financial card number will be saved."
                },
                "image_path": {
                    "type": "string",
                    "pattern": ".*/(.*\\.png)",
                    "default": "/data/credit-card.png",
                    "description": "Path to the image file containing the financial card number to be processed."
                }
            },
            "required": ["filename", "image_path"]
        }
    },

    {
        "name": "A9",
        "description": "Identify the source and destination files for finding similar comments.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Path to the input file containing comments."
                },
                "output_filename": {
                    "type": "string",
                    "description": "Path to the output file where the most similar comments will be saved."
                }
            },
            "required": ["filename", "output_filename"]
        }
    },

    {
        "name": "A10",
        "description": "Identify high-value (gold) ticket sales from a database and save them to a text file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.db)",
                    "default": "/data/ticket-sales.db"
                },
                "output_filename": {
                    "type": "string",
                    "pattern": r".*/(.*\.txt)",
                    "default": "/data/ticket-sales-gold.txt"
                },
                "query": {
                    "type": "string",
                    "pattern": "SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'"
                }
            },
            "required": ["filename", "output_filename", "query"]
        }
    },
    {
        "name": "B1",
        "description": "Ensures the task does not access content outside /data",
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "A plain-English task request. The system will validate that it does not attempt to access content outside /data."
                }
            },
            "required": ["task_description"]
        }
    },
    {
        "name": "B2",
        "description": "Ensure that no file or directory is deleted anywhere in the system, even if explicitly requested.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "A plain-English task description provided by the user."
                }
            },
            "required": ["task_description"]
        }
    },
    # {
    #     "name": "B3",
    #     "description": "Fetch data from an API and save it to a file.",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "api_url": {
    #                 "type": "string",
    #                 "pattern": "^https?://.*",
    #                 "description": "The API endpoint to fetch data from."
    #             },
    #             "output_filename": {
    #                 "type": "string",
    #                 "pattern": "^/data/.*",
    #                 "default": "/data/api-output.json",
    #                 "description": "Path to save the fetched data."
    #             },
    #             "headers": {
    #                 "type": "object",
    #                 "additionalProperties": { "type": "string" },
    #                 "description": "Optional headers to include in the API request."
    #             }
    #         },
    #         "required": ["api_url", "output_filename"]
    #     }
    # },

    # {
    #     "name": "B12",
    #     "description": "Check if filepath starts with /data",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "filepath": {
    #                 "type": "string",
    #                 "pattern": r"^/data/.*",
    #                 # "description": "Filepath must start with /data to ensure secure access."
    #             }
    #         },
    #         "required": ["filepath"]
    #     }
    # },
    {
        "name": "B3",
        "description": "Fetch data from an API and save it within the /data directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "api_url": {
                    "type": "string",
                    "pattern": "^https?://.*",
                    "description": "The API endpoint to fetch data from."
                },
                "output_filename": {
                    "type": "string",
                    "pattern": "^/data/.*",
                    "default": "/data/api-output.json",
                    "description": "Path within /data to save the fetched data."
                },
                "headers": {
                    "type": "object",
                    "additionalProperties": { "type": "string" },
                    "description": "Optional headers to include in the API request."
                }
            },
            "required": ["api_url", "output_filename"]
        }
    },
    {
        "name": "B4",
        "description": "Clone a Git repository inside /data and make a commit.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "pattern": "^(https|git)://.*\\.git$",
                    "description": "URL of the Git repository to clone."
                },
                "commit_message": {
                    "type": "string",
                    "default": "Automated commit by the agent",
                    "description": "Message for the commit."
                }
            },
            "required": ["repo_url"]
        }
    },

    {
        "name": "B5",
        "description": "Run a SQL query on a SQLite or DuckDB database and save the result.",
        "parameters": {
            "type": "object",
            "properties": {
                "db_filename": {
                    "type": "string",
                    "pattern": "^/data/.*\\.(db|duckdb)$",
                    "description": "Database file path (must be inside /data/)."
                },
                "query": {
                    "type": "string",
                    "description": "SQL query to execute. Only SELECT statements are allowed."
                },
                "output_filename": {
                    "type": "string",
                    "pattern": "^/data/.*\\.csv$",
                    "description": "Path to save query results (must be inside /data/)."
                }
            },
            "required": ["db_filename", "query", "output_filename"]
        }
    },

    {
        "name": "B6",
        "description": "Fetch content from a URL and save it to the specified output file.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "pattern": r"https?://.*",
                    "description": "URL to fetch content from."
                },
                "output_filename": {
                    "type": "string",
                    "pattern": r".*/.*",
                    "description": "Path to the file where the content will be saved."
                }
            },
            "required": ["url", "output_filename"]
        }
    },
    {
        "name": "B7",
        "description": "Compress or resize an image from /data/ and save the modified version.",
        "parameters": {
            "type": "object",
            "properties": {
                "input_filename": {
                    "type": "string",
                    "pattern": "^/data/.*\\.(jpg|jpeg|png)$",
                    "description": "Path of the image to be compressed/resized (must be in /data/)."
                },
                "output_filename": {
                    "type": "string",
                    "pattern": "^/data/.*\\.(jpg|jpeg|png)$",
                    "description": "Path to save the modified image (must be in /data/)."
                },
                "width": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "New width for resizing (optional, ignored if height is provided)."
                },
                "height": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "New height for resizing (optional, ignored if width is provided)."
                },
                "quality": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 100,
                    "default": 75,
                    "description": "Compression quality (JPEG only, ignored for PNG)."
                }
            },
            "required": ["input_filename", "output_filename"]
        }
    },
    {
        "name": "B8",
        "description": "Transcribe audio from an MP3 file and save the text.",
        "parameters": {
            "type": "object",
            "properties": {
                "input_filename": {
                    "type": "string",
                    "pattern": "^/data/.*\\.mp3$",
                    "description": "Path of the MP3 file to be transcribed (must be in /data/)."
                },
                "output_filename": {
                    "type": "string",
                    "pattern": "^/data/.*\\.txt$",
                    "description": "Path to save the transcribed text file (must be in /data/)."
                },
                "model": {
                    "type": "string",
                    "enum": ["whisper", "vosk"],
                    "default": "whisper",
                    "description": "Speech-to-text model to use (default: whisper)."
                }
            },
            "required": ["input_filename", "output_filename"]
        }
    },
    {
    "name": "B9",
    "description": "Convert a Markdown file to HTML and save the output.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_filename": {
                "type": "string",
                "pattern": "^/data/.*\\.md$",
                "description": "Path of the Markdown file to be converted (must be in /data/)."
            },
            "output_filename": {
                "type": "string",
                "pattern": "^/data/.*\\.html$",
                "description": "Path to save the converted HTML file (must be in /data/)."
            }
        },
        "required": ["input_filename", "output_filename"]
    }
},
{
    "name": "B10",
    "description": "Filter a CSV file based on a column value and return JSON data.",
    "parameters": {
        "type": "object",
        "properties": {
            "csv_filename": {
                "type": "string",
                "pattern": "^/data/.*\\.csv$",
                "description": "Path to the CSV file inside /data/."
            },
            "column_name": {
                "type": "string",
                "description": "The column to filter on."
            },
            "filter_value": {
                "type": "string",
                "description": "The value to match in the specified column."
            }
        },
        "required": ["csv_filename", "column_name", "filter_value"]
    }
}
]

def get_completions(prompt: str):
    print("Inside get_completions")#Debug
    with httpx.Client(timeout=20) as client:
        response = client.post(
            f"{openai_api_chat}",
            headers=headers,
            json=
                {
                    "model": "gpt-4o-mini",
                    "messages": [
                                    {"role": "system", "content": "You are a function classifier that extracts structured parameters from queries."},
                                    {"role": "user", "content": prompt}
                                ],
                    "tools": [
                                {
                                    "type": "function",
                                    "function": function
                                } for function in function_definitions_llm
                            ],
                    "tool_choice": "auto"
                },
        )

    print("DId suceessful llm calll")#Debug
    # return response.json()
    print("hlo")#Debug
    print(response.json())#Debug
    print(response.json()["choices"][0]["message"]["tool_calls"][0]["function"])
    return response.json()["choices"][0]["message"]["tool_calls"][0]["function"]


# Placeholder for task execution
@app.post("/run")
async def run_task(task: str):
    print()
    try:
        response = get_completions(task)
        print(f"Response THere: {response})")#Debug
        task_code = response['name']
        arguments = response['arguments']

        print("Task:",task_code)#Debug
        print(arguments)#Debug


        if "A1"== task_code:
            A1(**json.loads(arguments))
        if "A2"== task_code:
            A2(**json.loads(arguments))
        if "A3"== task_code:
            A3(**json.loads(arguments))
        if "A4"== task_code:
            A4(**json.loads(arguments))
        if "A5"== task_code:
            A5(**json.loads(arguments))
        if "A6"== task_code:
            A6(**json.loads(arguments))
        if "A7"== task_code:
            A7(**json.loads(arguments))
        if "A8"== task_code:
            A8(**json.loads(arguments))
        if "A9"== task_code:
            A9(**json.loads(arguments))
        if "A10"== task_code:
            A10(**json.loads(arguments))


        if "B1"== task_code:
            B1(**json.loads(arguments))
        if "B2"== task_code:
            B2(**json.loads(arguments))
        # if "B12"== task_code:
        #     B12(**json.loads(arguments))
        if "B3" == task_code:
            B3(**json.loads(arguments))
        if "B4" == task_code:
            B4(**json.loads(arguments))
        if "B5" == task_code:
            B5(**json.loads(arguments))
        if "B6" == task_code:
            B6(**json.loads(arguments))
        if "B7" == task_code:
            B7(**json.loads(arguments))
        if "B8" == task_code:
            B8(**json.loads(arguments))
        if "B9" == task_code:
            B9(**json.loads(arguments))
        if "B10" == task_code:
            B10(**json.loads(arguments))
        
        return {"message": f"{task_code} Task '{task}' executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Placeholder for file reading
@app.get("/read", response_class=PlainTextResponse)
async def read_file(path: str = Query(..., description="File path to read")):
    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)