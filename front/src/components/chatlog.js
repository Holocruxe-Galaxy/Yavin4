import React from 'react';
import Message from './message';

const ChatLog = ({ messages }) => (
  <div className="chatLog">
    {messages.map((message, index) => (
      <Message key={index} sender={message.sender} text={message.text} />
    ))}
  </div>
);

export default ChatLog;
