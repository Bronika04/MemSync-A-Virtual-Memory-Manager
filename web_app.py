from flask import Flask, render_template, request
from virtual_memory import VirtualMemoryManager

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    if request.method == "POST":
        pages = request.form["pages"]
        frames = int(request.form["frames"])

        vm = VirtualMemoryManager(frames)
        result = vm.simulate(pages.split())

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run()
