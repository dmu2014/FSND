import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import werkzeug
from werkzeug.exceptions import BadRequest, NotFound, UnprocessableEntity, InternalServerError
from werkzeug.wrappers import BaseRequest
from werkzeug.wsgi import responder
from models import Question, Category
from sqlalchemy.sql import func

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  app.config['SQLALCHEMY_ECHO'] = True  
  setup_db(app)
  
  '''
  @TODO-Done: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  cors = CORS(app, resources={r"*":{"origins": "*"}}) 

  '''
  @TODO-Done: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
    return response

  '''
  @TODO-Done: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def show_categories():
    try:    
      categoriesDict = {}
      categories = Category.query.with_entities(Category.type.label('type'), Category.id.label('id')).all()
      for category in categories:
        categoriesDict[category.id] = category.type
      
      return jsonify(
        {
          "success":True,
          "categories":categoriesDict
        }
      )
    except:
      abort(500)


  '''
  @TODO-Done: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions', methods=['GET'])
  def show_questions():           
    
      page = request.args.get('page', 1, type=int)
      start = (page - 1) * QUESTIONS_PER_PAGE
      end = page * QUESTIONS_PER_PAGE
      questions = Question.query.all()      
      total_questions = len(questions)      
      formatted_questions = [question.format() for question in questions][start:end]
      if(len(formatted_questions) < 1):
        abort(404)
      categoriesDict = {}
      categories = Category.query.with_entities(Category.type.label('type'), Category.id.label('id')).all()
      for category in categories:
        categoriesDict[category.id] = category.type
      current_category = Category.query.with_entities(Category.type.label('type')).first()

      return jsonify(
        {
          "success": True,
          "questions": formatted_questions,
          "total_questions": total_questions,
          "current_category": current_category,
          "categories": categoriesDict
        }
      )
    

  '''
  @TODO-Done: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:id>', methods=['DELETE'])
  def delete_question(id):
    try:
      question = Question.query.filter(Question.id == id).one_or_none()

      if(question is None):
        abort(404)

      question.delete()
      return jsonify(
        {
          "success": True
        }
      )
    except:
      abort(422)

  '''
  @TODO-Done: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/newquestion', methods=['POST'])
  def add_question():
    try:
      question = request.get_json().get('question', None)
      answer = request.get_json().get('answer', None)
      difficulty = request.get_json().get('difficulty', None)
      category = request.get_json().get('category', None)
      if(int(len(question)) < 1 or int(len(answer)) < 1 or difficulty is None or category is None):
        abort(422)      
      question = Question(question=question, answer=answer, difficulty=difficulty, category=category)
      question.insert()

      return jsonify(
        {
          "success":True
        }
      )
    except:
      abort(500)
      
       
  '''
  @TODO-Done: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions', methods=['POST'])
  def show_questions_by_searchTerm():
    try:
      searchTerm = request.get_json().get('searchTerm', '')
      questions = Question.query.filter(Question.question.ilike(f'%{searchTerm}%')).all()    
      formatted_questions = [question.format() for question in questions]
      total_questions = len(questions)
      current_category = request.get_json().get('currentCategory', '')
      return jsonify(
        {
          "success": True,
          "questions": formatted_questions, 
          "total_questions": total_questions,
          "current_category": current_category   
        }
      )
    except:
      abort(500)    

  '''
  @TODO-Done: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:id>/questions', methods=['GET'])
  def show_category_questions(id):
    try:
      current_category = Category.query.with_entities(Category.type.label("type")).filter(Category.id==id).one_or_none()
      if(current_category is None):
        abort(400)
      questions = Question.query.filter(Question.category==id).all()
      formatted_questions = [question.format() for question in questions]
      total_questions = len(questions)      

      return jsonify(
        {
          "success": True,
          "questions": formatted_questions, 
          "total_questions": total_questions,
          "current_category": current_category     
        }
      )
    except:
      abort(500)    


  '''
  @TODO-Done: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  of the previoand return a random questions within the given category, 
  if provided, and that is not one us questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    try:
      previous_questions = request.get_json().get('previous_questions', None) 
      quiz_category = request.get_json().get('quiz_category', None)

      category_questions=[]   
      nextQuestion={}

      if(quiz_category is None or (int(quiz_category.get('id')) < 1)):
        category_questions=Question.query.order_by(func.random()).all()      
      else:
        category_questions=Question.query.filter(Question.category==quiz_category.get('id')).order_by(func.random()).all()    

      for question in category_questions:
        if(question.id not in (previous_questions)):
          nextQuestion["id"]=question.id
          nextQuestion["question"]=question.question
          nextQuestion["answer"]=question.answer
          nextQuestion["category"]=question.category
          nextQuestion["difficulty"]=question.difficulty
          break  

      if (nextQuestion == {}):
        return jsonify(
        {
          "success": True          
        }
      )
      return jsonify(
        {
          "success": True,
          "question": nextQuestion
        }
      )
    except:
      abort(500)
      
  '''
  @TODO-Done: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify(
      {
        "success":False,
        "error":400,
        "message":"Bad Request"
      }
    ), 400

    @app.errorhandler(404)
    def not_found(error):
      return jsonify(
        {
          "success":False,
          "error":404,
          "message":"Not Found"
        }
      ), 404
      

    @app.errorhandler(422)
    def unprocessable_request(error):
      return jsonify(
        {
          "success":False,
          "error":422,
          "message":"Unprocessable Request"
        }
      ), 422

    @app.errorhandler(500)
    def internalserver_request(error):
      return jsonify(
        {
          "success":False,
          "error":500,
          "message":"Internal Server Error"
        }
      ), 500
  
  return app

    