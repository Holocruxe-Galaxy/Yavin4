import React, { Component } from 'react';
import './App.css';
import ChatLog from './components/chatlog';
import ChatInput from './components/chatinput';

class App extends Component {
  state = {
    userInput: "",
    chatLog: [],
    showDatabaseInputs: false
  }

handleSubmit = async () => {
  if (this.state.userInput.trim() === "") return;

  const userMessage = {
    sender: "user",
    text: this.state.userInput
  };

  this.setState(prevState => ({
    chatLog: [...prevState.chatLog, userMessage],
    userInput: ""
  }));


  try {
    const response = await fetch('http://localhost: 5000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: this.state.userInput })
    });

    const data = await response.json();
    const botMessage = {
      sender: "bot",
      text: data.response
    };

    this.setState(prevState => ({
      chatLog: [...prevState.chatLog, botMessage]
    }));
  } catch (error) {
    console.error("Error fetching chat response:", error);
  }
 
};

storeInDatabase = async () => {
  const questionInput = document.getElementById('question');
  const answerInput = document.getElementById('answer');
  const question = questionInput.value;
  const answer = answerInput.value;

  if (question.trim() === "" || answer.trim() === "") return;

  try {
    await fetch('http://localhost:5000/store', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question: question,
        answer: answer
      })
    });

    questionInput.value = '';
    answerInput.value = '';

    this.toggleDatabaseInputs();

  } catch (error) {
    console.error("Error storing data:", error);
  }
}


toggleDatabaseInputs = () => {
  this.setState(prevState => ({
    showDatabaseInputs: !prevState.showDatabaseInputs
  }));
}


render() {
  return (
    <div className="App">
      <div className="header">
        <h1>Welcome to HoloChat</h1>
        <p>Your futuristic chat experience.</p>
      </div>
      <div className="chat-container">
        <ChatLog messages={this.state.chatLog} />
        <ChatInput
          userInput={this.state.userInput}
          onInputChange={e => this.setState({ userInput: e.target.value })}
          onSubmit={this.handleSubmit}
        />
        <button onClick={this.toggleDatabaseInputs}>
          {this.state.showDatabaseInputs ? "Hide Database Inputs" : "Add to Database"}
        </button>
        {this.state.showDatabaseInputs && (
          <div class="input-container">
            <input id="question" placeholder="Question" />
            <input id="answer" placeholder="Answer" />
            <button onClick={this.storeInDatabase}>Store in Database</button>
          </div>
        )}
      </div>
    </div>
  );
}
}

export default App;
