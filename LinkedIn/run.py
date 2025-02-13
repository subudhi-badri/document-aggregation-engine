from flask import Flask, request, jsonify, render_template
from services.full_scrapper import scrape_full_profile
from services.search import search_with_name
import os
import json


app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        method = request.form["method"]
        if method == "direct":
            linkedin_id = request.form["linkedin_id"]
            profile_infos = scrape_full_profile(linkedin_id)
        else:
            name = request.form["name"]
            school_or_company = request.form["school_or_company"]
            print(f"Searching for LinkedIn ID using name: {name} and school/company: {school_or_company}")
            linkedin_id = search_with_name(name, school_or_company)
            print(f"LinkedIn ID found: {linkedin_id}")

            profile_infos = scrape_full_profile(linkedin_id) if linkedin_id else None

        
        # Assuming the output is saved in the profile_json directory
        if linkedin_id:
            output_file = f"services/outputs/profile_json/{linkedin_id}_profile.json"
        else:
            return jsonify({"error": "LinkedIn ID could not be found."}), 404


        
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                output_data = json.load(f)
            return jsonify(output_data)
        else:
            return jsonify({"error": "Profile data not found."}), 404

    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
