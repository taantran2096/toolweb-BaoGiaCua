from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# List to hold quotes
quotes = []

@app.route('/')
def index():
    return render_template('index.html', quotes=quotes)

@app.route('/add_quote', methods=['POST'])
def add_quote():
    new_quote = request.form['quote']
    quotes.append(new_quote)
    return redirect(url_for('index'))

@app.route('/edit_quote/<int:quote_id>', methods=['POST'])
def edit_quote(quote_id):
    quotes[quote_id] = request.form['quote']
    return redirect(url_for('index'))

@app.route('/export_pdf/<int:quote_id>')
def export_pdf(quote_id):
    # Logic for exporting quote to PDF using pdf_generator.py
    pass

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)