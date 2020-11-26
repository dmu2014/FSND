import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        self.newquestion = {
            "question": "Is this a new question?",
            "answer": "Yes",
            "difficulty": "1",
            "category":"1"
        }
        self.emptynewquestion = {
            "question": "",
            "answer": "",
            "difficulty": "",
            "category":""
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_paginated_questions(self):
        res = self.client().get('/questions')
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertEqual(len(data['questions']), 10) #QUESTIONS_PER_PAGE = 10
        self.assertTrue(data['current_category'])
        self.assertTrue(data['categories'])


    
    def test_get_questions_aborts404_when_page_outofbound(self):        
        res = self.client().get('/questions?page=1000')
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Not Found')   


    def test_showcategories(self):
        res = self.client().get('/categories')
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])

    def test_showcategories_aborts404_whenrequestFails(self):
        res = self.client().get('/categories/5')
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Not Found")    

    
    def test_delete_question(self):
        res = self.client().delete('/questions/2')
        data=json.loads(res.data)

        question = Question.query.filter(Question.id == 1).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(question, None)
    
    def test_delete_questions_aborts404_when_booknotfound(self):
        res = self.client().delete('/questions/1000')
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Not Found')    
    
    def test_create_new_question(self):
        res=self.client().post('/newquestion', json=self.newquestion)
        data=json.loads(res.data)
        newquestionstring = self.newquestion['question']
        insertedquestion=Question.query.filter(Question.question.ilike(f'{newquestionstring}')).first()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(self.newquestion['question'], insertedquestion.question)
        self.assertEqual(self.newquestion['answer'], insertedquestion.answer)
        self.assertEqual(int(self.newquestion['category']), insertedquestion.category)
        self.assertEqual(int(self.newquestion['difficulty']), insertedquestion.difficulty)    
    
    def test_createquestion_aborts400_emptybody(self):
        res=self.client().post('/newquestion', json=self.emptynewquestion)
        data=json.loads(res.data)        
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Bad Request')    

    def test_show_questions_search_term(self):
        res=self.client().post('/questions', json={"searchTerm":"auto", "currentCategory":"3"})
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])        
        self.assertTrue(data['current_category'])
        self.assertTrue(data['total_questions'])

    def test_show_questions_search_term_aborts500_when_requestfails(self):
        res=self.client().post('/questions')
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 500)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Internal Server Error")    

    def test_show_category_questions(self):
        res = self.client().get('/categories/1/questions')
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])        
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['current_category'])

    
    def test_show_category_questions_aborts400_categoryNotFound(self):
        res = self.client().get('/categories/5000/questions')
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertTrue(data['message'], "Bad Request")
    

    def test_quizzes_showsnextquestion(self):
        res=self.client().post('/quizzes', json={'previous_questions':[20,21], 'quiz_category':{'type':'Science', 'id':'1'}})
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 200)       
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])  

    def test_quizzes_showsnextquestion_aborts500(self):
        res=self.client().post('/quizzes', json={'malformed_previous_questions':[20,21], 'malformed_quiz_category':{'type':'Science', 'id':'1'}})
        data=json.loads(res.data)

        self.assertEqual(res.status_code, 500)       
        self.assertEqual(data['success'], False)
        self.assertTrue(data['message'], "Internal Server Error")

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()