from flask import render_template, request, jsonify, make_response
from flask.helpers import url_for
import pymongo
from tensorflow.keras.models import load_model
from numpy.core.fromnumeric import reshape, resize
from werkzeug.wrappers import response
from app import app
import cv2
import numpy as np
from PIL import Image
import io
# import re
import base64
from flask_pymongo import PyMongo
from datetime import date, datetime
from bson.objectid import ObjectId

app.config["MONGO_URI"] = "mongodb+srv://somkarunmongo:phoomteay@cluster0.q3poe.mongodb.net/Chest_X_Ray"

mongo = PyMongo(app)
db = mongo.db

img_size = 100

model = load_model('./model/CXR_COVID2.h5')
# print(model.summary())

label_dict = {0:'Covid19 Positive', 1: 'Covid19 Negative'}
predictv = ""
probabilityv = ""

def preprocess(img):
    img = np.array(img)

    if(img.ndim == 3):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    gray = gray/255
    resized = cv2.resize(gray, (img_size, img_size))
    reshaped = resized.reshape(1, img_size, img_size)
    return reshaped

@app.route('/')
@app.route('/index')
def index():
    return render_template('index3.html')

@app.route('/predict', methods=["POST", "OPTIONS"])
def predict():
    # print('HERE')
    #recive image data
    message = request.get_json(force=True)
    encoded = message['image']
    decoded = base64.b64decode(encoded)
    dataBytesIO = io.BytesIO(decoded)
    dataBytesIO.seek(0)
    #open image
    image = Image.open(dataBytesIO)
    #process image to AI
    test_image = preprocess(image)

    prediction = model.predict(test_image)
    result = np.argmax(prediction, axis=1)[0]
    accuracy = float(np.max(prediction, axis=1)[0])*100
    accuracy = "%.2f"%accuracy

    label = label_dict[result]

    # print(prediction, result, accuracy)
    global predictv 
    global probabilityv
    predictv = label
    probabilityv = accuracy
    
    

    response = {"prediction": {"result": label, "accuracy": accuracy}}

    if request.method == "OPTIONS": #CORS_Prefiight
        return _build_cors_prelight_response()
    elif request.method == "POST": #The actual request following the preflight
        # order = OrderModel.creator(....)
        return _corsify_actual_response(jsonify(response))
    else:
        raise RuntimeError("Weird - don't know how to handle method{}".format(request.method))    

    # return jsonify(response)



def _build_cors_prelight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route('/save_data', methods=["POST", "OPTIONS"])
def save_data():
    namev = request.form.get('paname') 
    surnamev = request.form.get('surname')
    sexv = request.form.get('sex')
    yobv = str(request.form.get('YOB'))
    ts = datetime.now()
    atkv = request.form.get('atk')
    atk_datev = request.form.get('atk_date')
    pcrv = request.form.get('pcr')
    pcr_datev = request.form.get('pcr_date')

    global predictv, probabilityv
    # probabilityv = round(probabilityv, 2)

    


    if 'img' in request.files:
        profile_image = request.files['img']
        mongo.save_file(profile_image.filename, profile_image)
        mongo.db.users.insert({
            'username': namev, 'surname': surnamev, 'sex': sexv, 'yob': yobv, 'predict': predictv, 'probability': probabilityv,
            'save_date': ts, 'profile_image_name': profile_image.filename,
            'atk': atkv, 'atk_date': atk_datev, 'pcr': pcrv, 'pcr_date': pcr_datev
         })
    
    return render_template('cxrlist.html')

@app.route('/file/<filename>')
def file(filename):
    return mongo.send_file(filename)


@app.route('/profile/<username>')
def profile(username):
    user = mongo.db.users.find_one_or_404({'username': username})
    surname = user['surname']
    sex = user['sex']
    yob = user['yob']
    predict = user['predict']
    save_date = user['save_date']
    probability = user['probability']
    # print(user['profile_image_name'])
    return f'''
        <h2>ชื่อ: {username} นามสกุล: {surname}</h2>
        <h2>เพศ: {sex}</h2>
        <h2>ปีเกิด: {yob}</h2>
        <h2>วันที่บันทึก: {save_date}</h2>
        <h2>คาดการณ์: {predict}</h2>
        <h2>โอกาส(%): {probability}</h2>
        <img src="{url_for('file', filename=user['profile_image_name'])}">
    '''

@app.route('/showdetail/<_id>')
def showdetail(_id):
    
    # user = mongo.db.users.find_one_or_404({'profile_image_name': profile_image_name})
    user = mongo.db.users.find_one_or_404({'_id': ObjectId(_id)})
    username = user['username']
    surname = user['surname']
    sex = user['sex']
    yob = user['yob']
    predict = user['predict']
    atk = user['atk']
    pcr = user['pcr']
    profile_image_name = user['profile_image_name']
    probability = user['probability']
    save_date = user['save_date']
    return f'''

        <a href="{url_for('index')}">กลับหน้าแรก</a>
        <a href="{url_for('cxrlist')}">ค้นหาข้อมูล</a>

        <p>-----------------------------------------------------------------</p>

        <h2>ชื่อ: {username} นามสกุล: {surname}</h2>
        <h3>เพศ: {sex}</h3>
        <h3>ปีเกิด: {yob}</h3>
        <h3>วันที่บันทึก: {save_date}</h3>
        <h3>คาดการณ์: {predict}</h3>
        <h3>โอกาส(%): {probability}</h3>
        <h3>ATK: {atk}</h3>
        <h3>RT-PCR: {pcr}</h3>
        <img width="1500" src="{url_for('file', filename=profile_image_name)}">
    '''

@app.route('/cxrlist')
def cxrlist():
    return render_template('cxrlist.html')

@app.route('/findpatient', methods=["POST", "OPTIOBNS"])
def findpatient():
    rname = request.form.get('rname')
    
    cxr_lists = db.users.find({'username':rname}).sort([('username', pymongo.ASCENDING),('surname', pymongo.ASCENDING), ('save_date', pymongo.ASCENDING)])
    clists = []
    sumclists = []
    vsurname = ""
    for cxr_list in cxr_lists:
        
        clists.append(cxr_list)
        if vsurname != cxr_list['surname']:
            sumclists.append({'username': cxr_list['username'], 'surname': cxr_list['surname']})

            vsurname = cxr_list['surname']

    # clen = len(clists)
    
    return render_template('cxrshow.html', clists=clists, sumclists=sumclists)
