# retail_project
Steps
install pip3
~pip3 install flask
pip3 install -U Flask-SQLAlchemy
sudo apt-get install mysql-server











Working
app = Flask //instantiating flask 
@app.route('/') 	//for routing
debug=true		//to reflect changes in code to browser automatically.
return (in route) is HTML code.
import render_template //to return a html file instead of writinh code directly
import request //to import get and post requests from html to python
return render_template(..., userDetails = ...) //this is use of jinja template to pass arguments to html code from python.
