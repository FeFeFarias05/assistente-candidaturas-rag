# Expense Dashboard

## Overview

Expense Dashboard is a personal project I built in 2025 to learn React while I was studying Software Engineering. I worked on it part-time for about six months, usually a few hours after classes and on weekends. My goal was to practice how to structure a small web app, display financial data clearly, and make the interface easy to use on a laptop and phone. The project started with a simple idea: show monthly expenses, category summaries, and recent transactions in one place.

## What I did

I built the interface with React using function components and hooks. I organized the screen into a header, summary cards, a transaction list, and a form to add new entries. I consumed the REST API with fetch and handled loading and error states. I did not use Redux; I managed state with hooks only. I also added basic filtering by category and month, plus simple validation so the form would not accept empty values or negative amounts. I spent time adjusting spacing, labels, and empty states so the dashboard stayed readable when there was little data. I did not write automated tests for the React components. I published the code on GitHub with a README in English.

## Results

By the end of the project, I had a working dashboard that could load expense data, add new items, and update the summary figures on the page. I finished it after roughly six months of part-time work in 2025. The main result was not just the final screen, but the practice of building a complete feature from the interface down to data handling. I also learned how to keep the code small enough to review later, which helped when I returned to the project after a break of one or two weeks.

## Challenges and learnings

The hardest part was dealing with changing states in a predictable way. When the data was still loading, I had to keep the page usable and avoid showing broken sections. Another challenge was keeping the form and list synchronized after each new expense was added. I learned to break the app into smaller pieces early, instead of growing one large component. I also learned that simple projects still need careful decisions about structure, naming, and error handling, especially when I am building and reviewing the code alone.
