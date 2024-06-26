from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, abort
# from turbo_flask import Turbo
from mvp_gui.models import *
from mvp_gui.ros_manager import *
from mvp_gui.gui_ros_manager import *
from mvp_gui.forms import *

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mvp_database.db'
app.config['SECRET_KEY'] = 'd5036a36d957701b9048179e'

# turbo = Turbo(app)

db.init_app(app)
app.app_context().push()

# Path to the directory where tiles are stored
TILES_DIR = "../offline_map/beach_pond_tiles_directory/"

global_file_name = './config/gui_config.yaml'

ros_source_base = "source /opt/ros/noetic/setup.bash && source catkin_ws/devel/setup.bash && "
roslaunch_folder_default = '~/catkin_ws/src/alpha_rise_auv/alpha_rise_bringup/launch/'

project_path = os.getcwd()
env = os.environ.copy()
env['PYTHONPATH'] = project_path

ssh_hostname = '192.168.0.118'
ssh_username = 'mingxi'
ssh_password = 'qwer1234'

# Create SSHConnection instance
ssh_connection = SSHConnection(ssh_hostname, ssh_username, ssh_password)


from mvp_gui.routes import routes_base
from mvp_gui.routes import routes_systems
from mvp_gui.routes import routes_rostopics
from mvp_gui.routes import routes_map
from mvp_gui.routes import routes_mission

