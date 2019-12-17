import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

## ROUTES

# Get drinks endpoint (short detail)
@app.route('/drinks')
def get_drinks():
    return jsonify({
        'success': True, 
        'drinks': [drink.short() for drink in Drink.query.all()]
    })

# Get drinks endpoint (long detail)
# Requires authorization
@app.route('/drinks-detail')
@requires_auth("get:drinks-detail")
def get_drinks_details(payload):
    return jsonify({
        'success': True, 
        'drinks': [drink.long() for drink in Drink.query.all()]
    })

# Post drinks endpoint 
# Requires authorization
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks(payload):
    body = request.get_json()

    title = body.get('title', None)
    recipe = body.get('recipe', None)

    try: 
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()

        new_drink = Drink.query.filter_by(id=drink.id).first()

        return jsonify({
            'success': True, 
            'drinks': new_drink.long()
        })

    except: 
        abort(422)

# Patch drinks endpoint 
# Requires authorization
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(payload, drink_id): 
    body = request.get_json()

    title = body.get('title', None)
    recipe = body.get('recipe', None)

    try: 
        drink = Drink.query.filter_by(id=drink_id).one_or_none()

        if drink is None:
            abort(404)

        if title is not None:
            drink.title = title

        if recipe is not None:
            drink.recipe = json.dumps(recipe)

        drink.update()

        drink_updated = Drink.query.filter_by(id=drink_id).first()

        return jsonify({ 
            'success': True, 
            'drinks': drink_updated.long()
        })

    except: 
        abort(422)

# Delete drinks endpoint 
# Requires authorization
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, drink_id): 
    try:
        drink = Drink.query.get(drink_id)
        if drink is None: 
            abort(404)

        drink.delete() 

        return jsonify({
            'success': True, 
            'delete': drink_id
        })

    except:
        abort(422)

## Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(404)
def not_found(error): 
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

@app.errorhandler(AuthError)
def auth_error(e):
    return jsonify(e.error), e.status_code
