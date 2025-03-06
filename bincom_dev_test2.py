from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)

# Configure MySQL Database Connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:didiudoh@localhost/bincom_test2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class PollingUnit(db.Model):
    __tablename__ = 'polling_unit'
    uniqueid = db.Column(db.Integer, primary_key=True)
    polling_unit_id = db.Column(db.Integer)
    ward_id = db.Column(db.Integer)
    lga_id = db.Column(db.Integer)
    
class AnnouncedPUResults(db.Model):
    __tablename__ = 'announced_pu_results'
    result_id = db.Column(db.Integer, primary_key=True)  # Corrected column name
    polling_unit_uniqueid = db.Column(db.Integer, db.ForeignKey('polling_unit.uniqueid'))
    party_abbreviation = db.Column(db.String(10))
    party_score = db.Column(db.Integer)

class LGA(db.Model):
    __tablename__ = 'lga'
    uniqueid = db.Column(db.Integer, primary_key=True)
    lga_name = db.Column(db.String(100))


@app.route('/polling_unit/<int:polling_unit_id>')
def polling_unit_results(polling_unit_id):
    results = AnnouncedPUResults.query.filter_by(polling_unit_uniqueid=polling_unit_id).all()

    # Debugging: Print results in the terminal
    print("Fetched Results:", results)  

    return render_template('polling_unit_results.html', results=results)


@app.route('/lga_results', methods=['GET', 'POST'])
def lga_results():
    lgas = LGA.query.all()
    results = None

    if request.method == "POST":
        selected_lga = request.form['lga_id']
        polling_units = PollingUnit.query.filter_by(lga_id=selected_lga).all()
        polling_unit_ids = [unit.uniqueid for unit in polling_units]

        results = db.session.query(
            AnnouncedPUResults.party_abbreviation,
            func.sum(AnnouncedPUResults.party_score).label('total_votes')
        ).filter(AnnouncedPUResults.polling_unit_uniqueid.in_(polling_unit_ids)).group_by(AnnouncedPUResults.party_abbreviation).all()

    return render_template('lga_results.html', lgas=lgas, results=results)


@app.route('/add_polling_unit', methods=['GET', 'POST'])
def add_polling_unit_results():
    if request.method == "POST":
        polling_unit_id = request.form["polling_unit"]
        print(f"Polling Unit ID: {polling_unit_id}")  # Debugging: Check submitted ID
        
        # Check if polling unit exists
        polling_unit = PollingUnit.query.filter_by(uniqueid=polling_unit_id).first()
        if not polling_unit:
            print(f"Polling unit with ID {polling_unit_id} does not exist.")  # Debugging
            return f"Polling unit with ID {polling_unit_id} does not exist.", 400

        # Print all form data to check if it's being sent properly
        print("Form data:", request.form)

        # Process form data and insert results
        for party in ["PDP", "APC", "LP", "NNPP"]:
            score = request.form.get(party, 0)
            print(f"Party: {party}, Score: {score}")  # Debugging

            try:
                score = int(score)
            except ValueError:
                print(f"Invalid score for {party}, setting to 0.")
                score = 0  

            new_result = AnnouncedPUResults(
                polling_unit_uniqueid=polling_unit_id, 
                party_abbreviation=party, 
                party_score=score,
                entered_by_user='admin'  
)
            db.session.add(new_result)

        try:
            db.session.commit()
            print("Results saved successfully!")  # Confirm successful save
            return redirect(url_for('polling_unit_results', polling_unit_id=polling_unit_id))
        except Exception as e:
            print(f"Error while committing to the database: {e}")
            db.session.rollback()
            return f"There was an error saving the results: {e}. Please try again.", 500

    polling_units = PollingUnit.query.all()
    return render_template('add_polling_unit.html', polling_units=polling_units)



if __name__ == "__main__":
    app.run(debug=True)
