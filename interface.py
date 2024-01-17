import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
pivot_df = pd.read_csv('pivot_df.csv')
study_plan=pd.read_csv('study_plan_cleaned.csv')
pivot_df
import pandas as pd
pivot_df.iloc[:, 1:-6] = pivot_df.iloc[:, 1:-6].applymap(lambda x: pd.NA if x == 0 else x)
min_grade = 35
pivot_df.iloc[:, 1:-6] = pivot_df.iloc[:, 1:-6].apply(lambda x: x - min_grade)
pivot_df['TAWJIH_GPA_normalized'] = (pivot_df['TAWJIH_GPA'] - 60) / (100 - 60)
pivot_df_filled = pivot_df.copy()
pivot_df_filled.iloc[:, 1:-6] = pivot_df_filled.iloc[:, 1:-6].fillna(0)
pivot_df_filled
unique_pairs = set(zip(study_plan['REQ_TYP'], study_plan['REQ_TYPEE']))
for req_number, req_description in unique_pairs:
    print(f"Requirement Type: {req_number}, Description: {req_description}")
unique_pairs = set(zip(study_plan['RULE_ID'], study_plan['RULE_DESC']))
for req_number, req_description in unique_pairs:
    print(f"Requirement Type: {req_number}, Description: {req_description}")
study_plan
columns_to_drop = ['COURSE_TYP', 'COURSE_TYPEE', 'LEVEL_ID', 'LEVEL_DESCE', 
                   'MARK_TYP', 'MARK_TYPEE', 'WEB_FLAG', 'LOAD_HOURS', 'REQ_HOURS','REQ_TYPEE','RULE_DESC']
study_plan = study_plan.drop(columns=columns_to_drop, axis=1)
updates = {
    14364: {'new_rule_id': 1, 'new_pre_course_id': 14270},
    14452: {'new_rule_id': 1, 'new_pre_course_id': 14350}
}
for course_id, update_info in updates.items():
    study_plan.loc[study_plan['COURSE_ID'] == course_id, 'RULE_ID'] = update_info['new_rule_id']
    study_plan.loc[study_plan['COURSE_ID'] == course_id, 'PRE_COURSE_ID'] = update_info['new_pre_course_id']
study_plan['PRE_COURSE_ID'] = study_plan['PRE_COURSE_ID'].fillna(0).astype(int)
study_plan
print(study_plan.dtypes)
grades = pivot_df_filled.iloc[:, 1:].values
user_similarity = cosine_similarity(grades)
user_similarity_df = pd.DataFrame(user_similarity, index=pivot_df_filled['STD_NO'], columns=pivot_df_filled['STD_NO'])
def check_course_rules(course_id, pivot_df, study_plan):
    course_info = study_plan[study_plan['COURSE_ID'] == course_id]
    if not course_info.empty:
        rule_id = course_info.iloc[0]['RULE_ID']
        pre_course_id = course_info.iloc[0]['PRE_COURSE_ID']
        if rule_id == 1:  
            if pre_course_id not in pivot_df.columns or pd.isna(pivot_df.at[pre_course_id]):
                return False  
        elif rule_id == 2:  
            return pre_course_id
    return True  
def generate_recommendations(user_id, user_similarity_df, pivot_df_filled, min_hours=9, max_hours=21):
    if user_id not in user_similarity_df.index:
        return "User ID not found in the dataset."
    user_similarities = user_similarity_df.loc[user_id]
    similar_users = user_similarities.sort_values(ascending=False).index
    watched_courses = pivot_df_filled[pivot_df_filled['STD_NO'] == user_id].dropna(axis=1).columns.tolist()
    course_scores = {}
    for similar_user in similar_users:
        if similar_user != user_id:
            similar_user_courses = pivot_df_filled[pivot_df_filled['STD_NO'] == similar_user].dropna(axis=1)
            for course in similar_user_courses:
                if course not in watched_courses and course != 'STD_NO':
                    course_rating = similar_user_courses[course].values[0]
                    course_scores[course] = course_scores.get(course, 0) + course_rating
    sorted_courses = sorted(course_scores, key=course_scores.get, reverse=True)
    recommended_courses = []
    total_hours = 0
    for course in sorted_courses:
        load_hour = int(str(course)[-1])
        course_id_int = int(str(course)[:-1])
        rule_check = check_course_rules(course_id_int, pivot_df_filled, study_plan)
        if rule_check is True or rule_check is not False:  # True or concurrent course ID
            recommended_courses.append(course)
            total_hours += load_hour
            if rule_check is not True:
                concurrent_course = str(rule_check) + str(load_hour)  # Assuming same load hour
                recommended_courses.append(concurrent_course)
                total_hours += load_hour
        if total_hours >= min_hours:
            break
    if total_hours < min_hours or total_hours > max_hours:
        return f"Unable to meet the hour requirement within 9-21 hours range."
    return recommended_courses
from flask import Flask, render_template, request
def generate_recommendations_web():
    user_input_id = request.form.get('student_id')
    user_input_rec = request.form.get('target_hours')
    try:
        user_id = int(user_input_id)
        target_hours = int(user_input_rec)
        if 9 <= target_hours <= 21:
            result = generate_recommendations(user_id, user_similarity_df, pivot_df, target_hours)
            if isinstance(result, str):
                return render_template('index.html', result=result)
            else:
                recommendations = []
                for course in result:
                    course_id_str = str(course).split('.')[0]
                    course_id_int = int(course_id_str[:-1])
                    course_desc = study_plan.loc[study_plan['COURSE_ID'] == course_id_int, 'COURSE_DESCE']
                    if not course_desc.empty:
                        recommendations.append({"course_id": course_id_int, "course_name": course_desc.iloc[0]})
                    else:
                        recommendations.append({"course_id": course_id_int, "course_name": "Not found"})
                return render_template('index.html', recommendations=recommendations)
        else:
            return render_template('index.html', result="Input must be between 9 and 21.")
    except ValueError:
        return render_template('index.html', error="Invalid input. Please enter valid values.")
app = Flask(__name__)
# the route to the the index.html page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return generate_recommendations_web()
    return render_template('index.html')
if __name__ == '__main__':
    app.run(debug=True)