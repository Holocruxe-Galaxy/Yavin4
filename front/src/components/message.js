import React from 'react';

const Message = ({ sender, text }) => (
  <div className={`message ${sender}`}>
    {sender === "user" ? "You: " : "HoloChat: "}{text}
  </div>
);

export default Message;
