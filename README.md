# 🏖️ CISC/CMPE 204 Modelling Project: Overflow

![Overflow game logo](https://static.wikia.nocookie.net/ajplaywild/images/c/cf/Minigame_splash_overflow.png/revision/latest?cb=20210522132908)

Welcome to Group 10's major project for CISC 204!

This is a solver for a game called Overflow, a mini-game inside of the popular massively multiplayer online game Animal Jam. The goal is to create a continuous path from the ocean at the top down to the moat of a sandcastle. This is accomplished by rotating square tiles containing either a straight path, curved path, or a bridge. Given the layout of a level, the solver finds a solution if one exists. In addition, it finds the longest possible path in order to maximize the number of points gained.

## 🌊 To run things


### Building

```bash
docker build -t cisc204
```

### Running

```bash
docker run -it -v $(pwd):/PROJECT cisc204
python3 overflow.py
```

Welcome to the major project for CISC/CMPE 204!

Change this README.md file to summarize your project, and provide pointers to the general structure of the repository. How you organize and build things (which files, how you structure things, etc) is entirely up to you! The only things you must keep in place are what is already listed in the **Structure** section below.

## 🏰 Structure

### General or provided

* `documents`: Contains folders for both of your draft and final submissions. README.md files are included in both.
* `run.py`: General wrapper script that you can choose to use or not. Only requirement is that you implement the one function inside of there for the auto-checks.
* `test.py`: Run this file to confirm that your submission has everything required. This essentially just means it will check for the right files and sufficient theory size.


### Custom code

* `overflow.py`: Contains the code to build and run the model.

