
// Get elements
const display = document.getElementById('display');
const clearButton = document.getElementById('clear');
const backspaceButton = document.getElementById('backspace');
// Function to update display
function updateDisplay(value) {
    display.value += value;
}
// Function to clear display
function clearDisplay() {
    display.value = '';
}
// Function to handle backspace
function handleBackspace() {
    const currentValue = display.value.slice(0, -1);
    display.value = currentValue;
}
// Event listeners
clearButton.addEventListener('click', () => {
    clearDisplay();
});
backspaceButton.addEventListener('click', handleBackspace);
// Number button event listener
document.querySelectorAll('.buttons button').forEach(button => {
    button.addEventListener('click', () => {
        updateDisplay(button.textContent);
    });
});
// Operator button event listeners
document.querySelectorAll('.operator-buttons button').forEach(button => {
    button.addEventListener('click', () => {
        if (display.value === '') return;
        const currentValue = display.value.slice(-1);
        display.value += button.textContent + currentValue;
    });
});