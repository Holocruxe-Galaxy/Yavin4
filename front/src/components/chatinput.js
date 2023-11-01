import React from 'react';

const ChatInput = ({ userInput, onInputChange, onSubmit }) => (
  <form className="chatInput" onSubmit={e => { e.preventDefault(); onSubmit(); }}>
    <input
      type="text"
      value={userInput}
      onChange={onInputChange}
    />
    <button type="submit">Send</button>
  </form>
);

export default ChatInput;
