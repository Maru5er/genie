from flask import Flask, jsonify, request, Response
from genie import Genie
import json

# create flask app
app = Flask(__name__)
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
    return genie.run()

@app.route('/stream', methods=['POST'])
def stream():
    if not request.is_json:
        return "Request body must be JSON", 400
    
    data = request.get_json()
    input = data.get('story')

    return Response(generate(input), mimetype='json')


if __name__ == '__main__':
    app.run(debug=True)