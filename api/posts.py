import base64
from datetime import datetime
import json
import os
import uuid

from h3 import point_dist
from flask import Blueprint, request, jsonify
from constants import INVALID_LOCATION, NO_LOCATION_GIVEN, NO_RADIUS_GIVEN
from utils import send_get_posts, send_upload_post, send_query, close_db

posts_api = Blueprint('posts_api', __name__)

IMAGE_DIR = os.environ["IMAGE_DIR"] + "/"

def str_tags(tags : list):
    '''Convert a list of tags to the string expected by the database'''
    tags = ":".join(tags)
    # Need to have a colon before ENDLIST if there are any tags
    if tags != "":
        tags += ":"
    return tags + "ENDLIST"

def is_location_valid(longitude, latitude):
    '''Verify that the latitude and longitude are valid'''
    return (float(latitude) >= -90 and
            float(latitude) <= 90 and
            float(longitude) >= -180 and
            float(longitude) <= 180)

def jsonify_get(res):
    '''Convert the result of a get request to a nice json object'''
    return [{"id": result[0],
            "latitude": result[2], 
            "longitude": result[3], 
            "poster": result[4], 
            "views": result[5], 
            "date": result[6],
            "tags": result[7]} for result in res]

def filter_location(json_results, latitude, longitude, radius):
    '''Filter the results of a get request by location'''
    filtered_results = []
    for result in json_results:
        if point_dist((latitude, longitude), (result["latitude"], result["longitude"])) <= radius:
            filtered_results.append(result)
    return filtered_results

@posts_api.route('/getImage', methods=['GET'])
def get_image():
    '''Get an image from the server by id'''
    id = request.args.get('id', None)
    if id is None:
        return "No id provided", 400
    
    try:
        url = send_query("SELECT ImageURL FROM Posts WHERE PostID = %s", [id])[0][0]
        image = base64.b64encode(open(IMAGE_DIR + url, 'rb').read())
        close_db()
        return image, 200
    except:
        return "Something went wrong...", 400

@posts_api.route('/getPosts', methods=['GET'])
def get_posts():
    start_time = datetime.now()
    '''Get posts from the database by location, page number, radius, and tags'''
    # Grab the arguments provided in the request
    tags = request.args.getlist('tags')
    latitude = request.args.get('latitude', None)
    longitude = request.args.get('longitude', None)
    radius = request.args.get('radius', None)
    pageNum = request.args.get('pageNum', None)
    cmd_params = []

    # Verify the locational arguments are valid
    if latitude is not None and longitude is not None:
        if not is_location_valid(longitude, latitude):
            return INVALID_LOCATION, 400
        if radius is None:
            return NO_RADIUS_GIVEN, 400
        # Append the latitude, longitude, and radius to the params since they are formatted correctly
        cmd_params += [latitude, longitude, radius]
    elif radius is not None:
        return NO_LOCATION_GIVEN, 400
    else:
        # If no location is given, grab all posts (negative radius means grab everything)
        cmd_params += [0, 0, -1]
    
    tags = str_tags(tags)
    cmd_params.append(tags)

    # Get the posts from the database based on the page number (if specified, otherwise get all posts)
    if pageNum is None:
        pageNum = 1
    else:
        pageNum = int(pageNum)
    cmd_params.insert(0, pageNum)
    res = send_get_posts(cmd_params)
    # If there are no results, return an empty list as the next steps are unnecessary
    if not res:
        return jsonify(res), 200
    
    response_json = jsonify_get(res)
    # Filter the results by location if a location was specified
    # Only have to check by radius because we already checked that the location was valid
    if radius is not None:
        response_json = filter_location(response_json, float(latitude), float(longitude), float(radius))

    # Set the tags for the result posts
    string_tuple = "(" + ",".join(["%s"] * len(res)) + ")"
    tag_list = send_query("SELECT Tag, PostID FROM Tags WHERE PostID IN " + string_tuple, tuple([result["id"] for result in res]))
    for result in res:
        result["tags"] = [tag[0] for tag in tag_list if tag[0] != "ENDLIST" and tag[1] == result["id"]]

    close_db()

    return jsonify(res), 200

@posts_api.route('/uploadPost', methods=['POST'])
def upload_post():
    '''Upload a post to the database and store the image in the file system'''
    # Grab the arguments provided in the request
    if request.form.get('tags', None) is not None:
        tags = json.loads(request.form.get('tags'))
    else: 
        tags = request.form.getlist('tags[]')
    user = request.form.get('user')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    # Ensure the latitude and longitude are specified correctly
    if not is_location_valid(longitude, latitude):
        return INVALID_LOCATION, 400

    # Upload image to the storage folder
    if request.files.get('image') is not None:
        image_bytes = request.files.get('image').read()
    else:
        image_bytes = base64.b64decode(request.form.get('image'))

    if image_bytes is None:
        return "No image provided", 400

    image_path = str(uuid.uuid4()) + ".png"
    with open(IMAGE_DIR + image_path, 'wb') as f:
        f.write(image_bytes)

    # Send the post to the database using the uploadPost stored procedure
    tags = str_tags(tags)
    cmd_params = [image_path, latitude, longitude, user, tags]
    send_upload_post(cmd_params)
    close_db()
    return "", 200

# @posts_api.route('/removePost/<id>', methods=['DELETE'])
# def remove_post(id):
#     res = send_query("DELETE FROM Posts WHERE PostID = %s", [id])
#     print("Res from delete is " + str(res))
#     return "", 200

# @posts_api.route('/viewPost/<id>', methods=['PATCH'])
# def view_post(id):
#     res = send_query("UPDATE Posts SET Views = Views + 1 WHERE PostID = %s", [id])
#     print("Res from update is " + str(res))
#     return "", 200

# @posts_api.route('/updatePost/<id>', methods=['PATCH'])
# def update_post(id):
#     '''Update a post in the database'''

#     return "", 200
