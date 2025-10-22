from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, ModelSettings ,set_tracing_disabled, function_tool, enable_verbose_stdout_logging
from openai import AsyncOpenAI
from dotenv import load_dotenv
import shutil
import os
import chainlit as cl


load_dotenv()
set_tracing_disabled(disabled=True)
# enable_verbose_stdout_logging()

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in environment variables. ")

external_client = AsyncOpenAI(
    api_key= gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model= OpenAIChatCompletionsModel(
    model= "gemini-2.5-flash",
    openai_client= external_client
)

config = RunConfig(
    model= model
)


@function_tool(strict_mode=False)
def file_and_folder_handler(
    file_name: str = None,
    folder_name: str = None,
    content: str = None,
    file_path: str = None,
    read: bool = None,
    delete: bool = None
):

    try:
        result_messages = []

        # ✅ Auto-detect path if only file_name is given
        if not file_path and file_name:
            file_path = os.path.join(folder_name, file_name) if folder_name else file_name

        # ✅ Create folder (if requested)
        if folder_name and not delete and not read:
            os.makedirs(folder_name, exist_ok=True)
            result_messages.append(f"📁 Folder '{folder_name}' is ready")

        # ✅ Delete file or folder
        if delete:
            if file_path and os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    result_messages.append(f"🗑️ File '{file_path}' deleted successfully")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    result_messages.append(f"🗑️ Folder '{file_path}' deleted successfully")
            else:
                result_messages.append(f"⚠️ Path '{file_path}' does not exist or not provided for deletion")

        # ✅ Read file (only read, no overwrite)
        if read and file_path:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    file_data = f.read()
                result_messages.append(f"📖 Content of '{file_path}':\n{file_data}")
                return "\n".join(result_messages)
            else:
                result_messages.append(f"⚠️ File '{file_path}' does not exist")
                return "\n".join(result_messages)

        # ✅ Create or write to file (only if not in read/delete mode)
        if file_name and not delete and not read:
            if folder_name:
                full_path = os.path.join(folder_name, file_name)
            else:
                full_path = file_name

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content if content else "")

            result_messages.append(f"📝 File '{full_path}' created successfully")
            if content:
                result_messages.append(f"✏️ Content written to '{full_path}'")

        return "\n".join(result_messages) if result_messages else "No action performed."

    except Exception as e:
        return f"❌ Error occurred: {e}"


file_handler_agent = Agent(
    name= "FileHandlerAgent",
    instructions= """you are helpfull file management assistant.You can:
    1. Create folders and files
    2. Write content to files
    3. Read content from files
    4. You should use the tool to perform file and folder operations
    5. Generate HTML, CSS JS code snippets when required
    
    Examples of what you can do:
    - Create a folder named 'my_project'
    - Inside 'my_project', create a file named 'index.html' with a basic HTML template
    - Read the content of 'my_project/index.html'
    - Delete the file 'my_project/index.html'
    - Remove the folder 'my_project' """,
    model= model,
    # model_settings= ModelSettings(tool_choice= "auto")
    tools=[file_and_folder_handler],
    
)

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content= "Assalamualaikum! File Manager is here").send()

@cl.on_message
async def on_message(message: cl.Message):
    result= await Runner.run(
        starting_agent= file_handler_agent,
        input= message.content
    )
    await cl.Message(content=result.final_output).send()




# <<<<<<<<<<<<<< This code is just for only cli use case >>>>>>>>>>>>>>>
  
# prompt=input("How can I help you today?")
# result= Runner.run_sync(
#     starting_agent= file_handler_agent,
#     # input= "create three file html css and js in folder named full_stack",
#     # input= "create a folder named 'test_folder' and inside it create a file named todo_list.htlm and write a html todo list with 3 items in it. and then read the content of the file and print it. ",
#     # input= "create a file named index.html with animated modern and attractive ui todo list with code and also good css styling. ",
#     # input= "create a full stack portfolio website using html and css with animated modern ui and each every functionality should be in fully working mode. ",
#    input= prompt,
#    max_turns= 20,
#     run_config= config
# )

# print(result.final_output)
