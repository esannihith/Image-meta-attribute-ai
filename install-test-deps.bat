@echo off
echo Installing test dependencies for frontend...
cd frontend
npm install --save-dev vitest @testing-library/react @testing-library/react-hooks @testing-library/dom @testing-library/user-event @babel/eslint-parser eslint
echo Finished installing test dependencies.
pause
