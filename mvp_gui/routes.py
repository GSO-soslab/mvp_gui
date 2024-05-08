import json
from mvp_gui import *
from mvp_gui.forms import WaypointForm
import xml.etree.ElementTree as ET


@app.context_processor
def inject_load():
    vitals = Vitals.query.first()
    poses = Poses.query.first()
    items = PowerItems.query.all()
    return {'vitals': vitals, 'poses': poses, 'items': items}


# routes
@app.route("/", methods=['GET', 'POST'])
def home_page():
    vitals = Vitals.query.first()
    poses = Poses.query.first()
    return render_template("home.html", vitals=vitals, poses=poses)


@app.route("/power_manager",  methods=['GET', 'POST']) 
def power_manager_page():
    vitals = Vitals.query.first()
    items = PowerItems.query.all()
    # print("power manager")
    if request.method == 'POST':
        action = request.form.get('action')
        for item in items:
            # print(str(item.id))
            if action == str(item.id):
                if item.status == 'On':
                    item.status = 'Off'
                    db.session.commit()
                    ##call rosservice
                else:
                    item.status = "On"
                    db.session.commit()
                    ##call rosservice
            # return render_template("power_manager.html", items=items, vitals=vitals)
    return render_template("power_manager.html", items=items, vitals=vitals)


@app.route('/waypoint_drag', methods=['POST'])
def waypoint_drag():
    ##map actions
    js_data = request.json
    js_lon = js_data['lng']
    js_lat = js_data['lat']
    entry = Waypoints.query.get(js_data['id'])
    entry.lat= js_lat
    entry.lon = js_lon
    db.session.commit()

    return redirect(url_for('map_page'))

@app.route("/mission", methods=['GET', 'POST'])
def mission_page():
    ## sort the waypoints by id
    waypoints = Waypoints.query.order_by(Waypoints.id).all()

    ##reassign the ID from 1 to N
    count = 1
    for entry in waypoints:
        entry.id = count
        count = count + 1
        db.session.commit()

    #button actiions
    if request.method == 'POST':
        # action = request.form.get('action')
        if 'add' in request.form:
            return redirect(url_for('add_waypoint_page')) 

        elif 'publish' in request.form:
            print("waypoint publish")

        ##delete a waypoint
        elif 'delete' in request.form:
            delete_id = request.form['delete']
            entry = Waypoints.query.get(delete_id)
            if entry:
                db.session.delete(entry)
                db.session.commit()
                return redirect(url_for('mission_page'))
    
        ##edit a waypoint
        elif 'edit' in request.form:
            edit_id = request.form['edit']
            return redirect(url_for('edit_waypoint_page', edit_id=edit_id)) 
        
        elif 'copy' in request.form:
            edit_id = request.form['copy']
            entry = Waypoints.query.get(edit_id)
            new_entry = Waypoints()
            new_entry.id = len(waypoints)+1 #already obtained before
            new_entry.lat = entry.lat
            new_entry.lon = entry.lon
            new_entry.z = entry.z

            db.session.add(new_entry)
            db.session.commit()
            return redirect(url_for('mission_page'))
        
    ##render the mission site
    return render_template("mission.html", items=waypoints)

def generat_waypoints_from_kml(file_name, replace_flag):
    tree = ET.parse(file_name)
    root = tree.getroot()

    waypoints = Waypoints.query.all()
    id_data = len(waypoints)+1

    if replace_flag ==1:
        id_data=1
    new_waypoints = []
    for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
        coordinates = placemark.find('.//{http://www.opengis.net/kml/2.2}coordinates').text
        # Splitting coordinates into latitude, longitude, and altitude
        lon, lat, z = map(float, coordinates.split(','))
        new_waypoints.append({'id': id_data, 'lat': lat, 'lon': lon, 'z': z})
        id_data = id_data +1
    if replace_flag == 1:
        db.session.query(Waypoints).delete()

    for waypoint_data in new_waypoints:
        waypoint = Waypoints(id=waypoint_data['id'],
                            lat=waypoint_data['lat'],
                            lon=waypoint_data['lon'],
                            z=waypoint_data['z'])
        db.session.add(waypoint)
    db.session.commit()
    

@app.route('/mission/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'replace':
        # if request.form.get('replace'):
            # print("replace pressed")
            if 'fileToUpload' not in request.files:
                return 'No file part'
            file = request.files['fileToUpload']
            if file.filename == '':
                return 'No selected file'
            ##do something
            if file:
                file.save('uploads/' + file.filename)
                generat_waypoints_from_kml('uploads/' + file.filename, 1)

        elif action == 'append':
        # elif request.form.get('append'):
            # print("append pressed")
            if 'fileToUpload' not in request.files:
                return 'No file part'
            file = request.files['fileToUpload']
            if file.filename == '':
                return 'No selected file'
            if file:
                file.save('uploads/' + file.filename)
                generat_waypoints_from_kml('uploads/' + file.filename, 0)
    return redirect(url_for('mission_page'))
    


@app.route('/mission/edit_waypoint', methods=['GET','POST'])
def edit_waypoint_page():
    edit_id = request.args.get('edit_id')
    entry = Waypoints.query.get(edit_id)
    form = WaypointForm()

    ## if submit pressed
    if form.validate_on_submit():
        entry.id = form.id.data
        entry.lat = form.lat.data
        entry.lon = form.lon.data
        entry.z = form.z.data
        db.session.commit()
        return redirect(url_for('mission_page'))
    return render_template('edit_waypoints.html', form=form, entry=entry)


@app.route('/mission/waypoints', methods=['GET','POST'])
def add_waypoint_page():
    form = WaypointForm()
    waypoints = Waypoints.query.all()
    id_data = len(waypoints)+1

    ## if submit pressed
    if form.validate_on_submit():
        ##get values    
        waypoint = Waypoints(id=id_data,
                           lat=form.lat.data,
                           lon=form.lon.data,
                           z=form.z.data,
                           )
        db.session.add(waypoint)
        db.session.commit()
        return redirect(url_for('mission_page'))
    return render_template('add_waypoints.html', form=form)


@app.route('/map', methods=['GET','POST'])
def map_page():
     ##get vehilce lat lon for map
    poses = Poses.query.first()
    vehicle_data = {
            "lat": float(poses.lat),
            "lon": float(poses.lon)
        }

    ## sort the waypoints by id
    waypoints = Waypoints.query.order_by(Waypoints.id).all()
    waypoints_data = []
    for waypoint in waypoints:
        waypoint_dict = {
            "id": waypoint.id,
            "lat": float(waypoint.lat),
            "lon": float(waypoint.lon)
        }
        waypoints_data.append(waypoint_dict)
    return render_template("map.html", items_jsn=waypoints_data, vehicle_jsn=vehicle_data)


@app.route("/monitor")
def monitor_page():
    return render_template("monitor.html")






