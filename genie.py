from openai import OpenAI, AssistantEventHandler
from dotenv import load_dotenv
from typing_extensions import override
from pydub import AudioSegment
import io
import json

class Genie:
  def __init__(self):
    load_dotenv()
    self.client = OpenAI()

    example_json = {
      "images" : [
        {
          "src" : "https://sampleurl.com",
          "caption" : "sample description"
        }
      ]
    }

    sample_description = """
    Setting : in a coffee shop
    Time : day time
    Character : A man with a black shirt and a child with a lollipop
  """

    # initializing assistant
    self.assistant = self.client.beta.assistants.create(
    model="gpt-4o",
    response_format={"type" : "json_object"},
    instructions=f"""
      You are an expert illustrator. Your task is to generate images to supplement the story from given input text. 
      Make sure the description of the image is accurate and as specific as possible. Your description should also be family friendly.
      Make sure the image description has the same form as follows : {sample_description}
      You have to output in valid JSON. The data schema should be as follows : {json.dumps(example_json)}.
      Keep the caption returned in the JSON short      
    """,
    tools=[{
        "type": "function",
        "function": {
          "name": "generate_images",
          "description": "Generate image based on the given text.",
          "parameters": {
            "type": "object",
            "properties": {
              "input": {
                "type": "string",
                "description": "Descriptive text of the image to generate"
              },
              "style" : {
                "type" : "string",
                "description" : "The style of image to be generated"
              },
            },
            "required": ["input", "style"]
          }
        }
      },
      ],
    name="Illustrator",
  )
    
    
  # parse audio
  # output : transcription for the audio
  def transcribe_audio(self, audio_file):
    audio_bytes = audio_file.read()
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
    #transcript = self.client.audio.translations.create(
      #model="whisper-1",
      #file=audio
    #)
    return "Hello"


    
  # input : user message
  def create_thread(self, input):
    self.thread = self.client.beta.threads.create()
    self.messages = self.client.beta.threads.messages.create(
      thread_id=self.thread.id,
      role="user",
      content=input
    )

  # run thread
  # TODO: return image binaries instead of markdown text
  def run(self):
    if self.thread == None or self.messages == None:
      raise Exception("Thread not initialized. Run create_thread first")
    
    event_handler = EventHandler(self.client)
    with self.client.beta.threads.runs.stream(
      thread_id=self.thread.id,
      assistant_id=self.assistant.id,
      event_handler=event_handler
    ) as stream:
      stream.until_done()
      result = ''.join(event_handler.accumulated_text)
    return result
    

# Event Handler class for assistant   
class EventHandler(AssistantEventHandler):
  def __init__(self, client):
    super().__init__()
    self.client = client
    self.accumulated_text = []

  @override
  def on_event(self, event):
    # Retrieve events that are denoted with 'requires_action'
    # since these will have our tool_calls
    if event.event == 'thread.run.requires_action':
      run_id = event.data.id  # Retrieve the run ID from the event data
      self.handle_requires_action(event.data, run_id)

  # generate image based on input description and style
  # on success, return openai image.data
  # on error, return None
  # TODO: return image binary maybe?
  def generate_images(self, input, style):
    try:
      dalle = self.client.images.generate(
        model="dall-e-3",
        prompt=f"Generate image in a {style} style. DO NOT add any detail, just use it AS-IS. {input}",
        size="1024x1024",
        quality="standard",
        n=1
      )
      return dalle.data
    except:
      return None
    
  def parser(self, images, descriptions):
    result = {}
    for i in range(len(images)):
      result[i] = {
        images[i] : descriptions[i]
      }
    json_obj = json.dumps(result)
    return json_obj

  def handle_requires_action(self, data, run_id):
    tool_outputs = []
      
    for tool in data.required_action.submit_tool_outputs.tool_calls:
      if tool.function.name == "generate_images":
        arguments = json.loads(tool.function.arguments)
        prompt = arguments["input"]
        style = arguments["style"]
        images = self.generate_images(prompt, style)
        if (images != None):
          for image in images:
            if image == None:
              tool_outputs.append({"tool_outputs" : tool.id, "output" : "violation"})
              break
          for image in images:
            tool_outputs.append({"tool_call_id": tool.id, "output": image.url})
        else :
          tool_outputs.append({"tool_outputs" : tool.id, "output" : "violation"})
      
    # Submit all tool_outputs at the same time
    self.submit_tool_outputs(tool_outputs, run_id)

  def submit_tool_outputs(self, tool_outputs, run_id):
    # Use the submit_tool_outputs_stream helper
    with self.client.beta.threads.runs.submit_tool_outputs_stream(
      thread_id=self.current_run.thread_id,
      run_id=self.current_run.id,
      tool_outputs=tool_outputs,
      event_handler=EventHandler(self.client),
    ) as stream:
      for text in stream.text_deltas:
        self.accumulated_text.append(text)
      