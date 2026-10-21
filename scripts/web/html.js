// JSX without a build step: html`<${Component} prop=${x}>...</${Component}>`.
import React from "react";
import htm from "htm";

export const html = htm.bind(React.createElement);
