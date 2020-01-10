inputField = document.getElementById("field-username");
inputForm = document.getElementById("form");
submitButton = document.getElementById("submit");
message = document.getElementById("message");

// Remove input field placeholder if the text field is not empty
let switchClass = function(input) {
  if (input.value.length > 0) {
    input.classList.add('has-contents');
  }
  else {
    input.classList.remove('has-contents');
  }
};

// Submit username and receive response
let showMessage = function(messageText) {
  // Unhide the message text
  message.classList.remove("hidden");

  message.innerHTML = messageText;
};

let onResponse = function(response, success) {
  // Display message
  showMessage(response);

  if(success) {
    // Hide input field and submit button
    form.classList.add("hidden");

    // Redirect after a sec
    return;
  }

  // Enable submit button and input field
  submitButton.classList.remove('button--disabled');
  submitButton.value = "Submit"
};

var dummyBool = false;
let submitUsername = function(username) {
  if(username.length == 0) {
    onResponse("Please enter a username.", false);
    return;
  }
  setTimeout(() => {
    if(dummyBool) {
      onResponse("This username is not available, please choose another.", false);
    } else {
      onResponse("Success. Please wait a moment for your browser to redirect.", true);
    }
  }, 750);
  dummyBool = !dummyBool;
}

let clickSubmit = function() {
  if(submitButton.classList.contains('button--disabled')) { return; }

  // Disable submit button and input field
  submitButton.classList.add('button--disabled');

  // Submit username
  submitButton.value = "Checking...";
  submitUsername(inputField.value);
};

submitButton.onclick = clickSubmit;

// Listen for events on inputField
inputField.addEventListener('keyup', function(event) {
  // Listen for Enter on input field
  if(event.which === 13) {
    clickSubmit();
    return;
  }
  switchClass(inputField);
});
inputField.addEventListener('change', function() {
  switchClass(inputField);
});

