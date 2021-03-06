import os
from app import app
from flask import flash, render_template, request, redirect, url_for, session
from app.models import newsUtils, stocksUtils
from flask_pymongo import PyMongo

app.config['MONGO_DBNAME'] = "final_project_test"
app.config['MONGO_URI'] = "mongodb+srv://admin:nZ0ELdTyXc6f5utn@cluster0-wb3wx.mongodb.net/final_project_test?retryWrites=true&w=majority"
mongo = PyMongo(app)

# USERS
def getUserData(username):
    collection = mongo.db.user_database
    users = list(collection.find({"username":username}))
    if len(users) == 0:
        return -1
    else:
        return users[0]

def getUserId(username):
    collection = mongo.db.user_database
    users = list(collection.find({"username":username}))
    if len(users) == 0:
        return -1
    else:
        return users[0]["userId"]

def authenticateUser(username, password):
    user = getUserData(username)
    if not user == -1:
        if user["username"] == username and user["password"] == password:
            return True
    return False
    
def addUser(username, password):
    collection = mongo.db.user_database
    users = list(collection.find({}))
    userId = len(users) + 1
    collection.insert({
        "userId": userId,
        "username": username,
        "password": password,
        "savedArticles": [],
        "savedStocks": []
    })
    return userId        
        
def editUserData(username, params):
    collection = mongo.db.user_database
    collection.update_one({"username": username}, { "$set": params })
    
# ARTICLES CURRENTLY VIEWING
def getCurrentArticles(username):
    collection = mongo.db.current_articles
    users = list(collection.find({"username": username}))
    if len(users) == 0:
        return -1
    else:
        print(users[0]["articles"])
        return users[0]["articles"]    
    
def saveCurrentArticles(username, articles):
    collection = mongo.db.current_articles
    if getCurrentArticles(username) == -1:
        collection.insert({
            "username": username,
            "articles": articles
        })
    else:
        collection.update_one(
            {"username": username}, 
            { "$set": {"articles": articles }}
        )

app.secret_key = "secret_key"
# STARTING PAGE
@app.route("/")
# NEWS API KEY: 12126d1b282e4c94a45c9a108b94f246
def start():
    if not "username" in session:
        return redirect(url_for("news"))
    else:
        return redirect(url_for("home"))

# NAVBAR OPTIONS
@app.route("/home", methods=["GET"])
def home():
    if not "username" in session:
        return redirect(url_for("login"))
    else:
        userData = getUserData(session["username"])
        articlesList = userData["savedArticles"]
        stocksList = userData["savedStocks"]
        #stocksList = ["aapl", "amd"]
        return render_template("home.html", logged = True, articlesList=articlesList, stocksList=stocksList)

@app.route("/news", methods=["GET"])
def news():
    logged = "username" in session
    # sitesList = newsUtils.getSiteList(10)
    # articlesList = []
    # for site in sitesList:
    #     siteId = newsUtils.idDict[site]
    #     article = newsUtils.getTopResponse(siteId)
    #     articlesList.append(article)
    #articlesList = newsUtils.getArticles(3)
    articlesList = newsUtils.cleanImg(newsUtils.getArticles(3))
    for index in range(0, len(articlesList)):
        articlesList[index]["index"] = index
    for article in articlesList:
            if article["author"] == None or "https:" in article["author"]:
                article["author"] = article["source"]["name"]
            elif not(article["source"]["name"] in article["author"]):
                article["author"] = article["author"] + ", " + article["source"]["name"]
    if logged:
        # session cookie sometimes too
        #session["articles"] = articlesList
        saveCurrentArticles(session["username"], articlesList)
    return render_template("news.html", articlesList=articlesList, logged=logged)


@app.route("/finance", methods=["GET","POST"])
def finance():
    logged = "username" in session
    print("LOGGED? ", logged)
    articlesList = []
    search = False
    symbol = ""
    if "symbol" in request.form:
        symbol = request.form["symbol"]
        if symbol == "":
            symbol = "aapl"
        search = True
        articlesList = stocksUtils.getStockArticles(symbol, 10)
        for index in range(0, len(articlesList)):
            articlesList[index]["index"] = index
            print(articlesList[index]["index"])
        if logged:
            #session["articles"] = articlesList
            saveCurrentArticles(session["username"], articlesList)
    return render_template("searchFinance.html", logged=logged, articlesList=articlesList, search=search, symbol=symbol)

@app.route("/about", methods=["GET"])
def about():
    logged = "username" in session
    return render_template("about.html", logged=logged)
    
# SEARCH REQUESTS
@app.route("/news/search", methods=["GET","POST"])
def searchNews():
    logged = "username" in session
    articlesList = []
    if "query" in request.form:
        query = request.form["query"]
        if query == "":
            query = "North Korea"
        articlesList = newsUtils.getArticlesByQuery(query)
        for index in range(0, len(articlesList)):
            articlesList[index]["index"] = index
        for article in articlesList:
            if article["author"] == None or "https:" in article["author"]:
                article["author"] = article["source"]["name"]
            elif not(article["source"]["name"] in article["author"]):
                article["author"] = article["author"] + ", " + article["source"]["name"]
        if logged:
            #session["articles"] = articlesList
            saveCurrentArticles(session["username"], articlesList)
    return render_template("searchNews.html", articlesList=articlesList, logged=logged)
    
# @app.route("/finance/search", methods=["GET"])
# def searchFinance():
#     logged = "username" in session
#     symbol = request.args["symbol"]
#     articlesList = stocksUtils.getStockArticles(symbol, 5)
#     for index in range(0, len(articlesList)):
#         articlesList[index]["index"] = index
#         print(articlesList[index]["index"])
#     if logged:
#         session["articles"] = articlesList
#     return render_template("searchFinance.html", articlesList=articlesList)

# AUTHENTICATION
@app.route("/register", methods=["GET", "POST"])
def register():
    return render_template("register.html")

@app.route("/register/auth", methods=["POST"]) ##
def register_auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm"]
        
        if getUserId(username) == -1:
            if password == confirm:
                addUser(username, password)
                flash("ACCOUNT SUCCESSFULLY CREATED")
                return redirect(url_for("login"))
            else:
                flash("PASSWORDS DO NOT MATCH")
        else:
            flash("USERNAME TAKEN")
    return redirect(url_for("register"))
    

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")

@app.route("/login/auth", methods=["POST"]) ##
def login_auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if authenticateUser(username, password):
            session["username"] = username
            return redirect(url_for("home"))
        else:
            flash("INCORRECT USERNAME OR PASSWORD")
    return redirect(url_for("login"))

@app.route("/logout", methods=["GET"])
def logout():
    if "username" in session:
        session.pop("username")
    if "articles" in session:
        session.pop("articles")
    return redirect(url_for("news"))
    
# SAVE REQUESTS
# Change to 
# finance/save/article
# news/save/article
@app.route("/save/article", methods=["GET", "POST"])
def saveArticle():
    if "username" in session:
    #and "articles" in session:
        username = session["username"]
        index = int(request.args["index"])
        
        articleToSave = getCurrentArticles(username)[index]
        print("ARTICLE TO SAVE", articleToSave)
        #articleToSave = session["articles"][index]
        userData = getUserData(username)
        savedArticles = userData["savedArticles"]
        savedArticles.append(articleToSave)
        
        editUserData(username, {
            "savedArticles": savedArticles
        })
    return redirect(url_for("home"))
    
@app.route("/save/stock", methods=["GET", "POST"])
def saveStock():
    if "username" in session:
        username = session["username"]
        stock = request.args["symbol"]
        if stock == "":
            stock = "aapl"
        userData = getUserData(username)
        savedStocks = userData["savedStocks"]
        if stock not in savedStocks:
            savedStocks.append(stock)
            
            editUserData(username, {
                "savedStocks": savedStocks
            })
    return redirect("/home#stocks")

@app.route("/contact", methods=["GET","POST"])
def contact():
    
    if request.method == "GET":
        return render_template('about.html')
    else:
        name = request.form["name"]
        email = request.form["email"]
        feedback = request.form["feedback"]
        collection = mongo.db.feedback
        collection.insert({
            "name": name, 
            "email": email,
            "feedback": feedback
        })
        flash("Your response has been recorded!")
        return redirect(url_for("about"))