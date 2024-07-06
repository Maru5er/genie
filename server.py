from flask import Flask, jsonify, request, Response
from genie import Genie
from flask_cors import CORS
import json

# create flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], allow_headers=[
    "Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True)
genie = Genie()

# on the terminal type: curl http://127.0.0.1:5000/ 
# returns hello world when we use GET. 
# returns the data that we send when we use POST. 
@app.route('/', methods = ['GET', 'POST']) 
def home(): 
    if(request.method == 'GET'): 
  
        data = "hello world"
        return jsonify({'data': data})
    
def generate(input):
    genie.create_thread(input)
    output = genie.run()
    if (output == '') :
        bad_request = {
        "images" : [
                {
                "src" : "https://img.freepik.com/free-vector/crossing-bones-skull-vector-logo_43623-1281.jpg?size=338&ext=jpg&ga=GA1.1.2113030492.1720137600&semt=sph",
                "caption" : "your story violates the community guidelines"
                }
            ]}
        return json.dumps(bad_request)
    return output

@app.route('/stream', methods=['POST'])
def stream():
    if not request.is_json:
        return "Request body must be JSON", 400
    
    data = request.get_json()
    input = data.get('story')

    return Response(generate(input), mimetype='json')


if __name__ == '__main__':
    app.run(debug=True)