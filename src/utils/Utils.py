from flask import jsonify

class Utils:

    @classmethod
    def create_response(self, message, success, status_code):
        response = jsonify({
            'message': message,
            'success': success
        })
        return response, status_code
