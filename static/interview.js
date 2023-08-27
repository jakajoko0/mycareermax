// When the form is submitted...
$("#interview-form").on("submit", function (event) {
  event.preventDefault();

  var formData = new FormData();
  formData.append("job_title", $("#job_title").val());
  formData.append("job_description", $("#job_description").val());
  formData.append("job_requirements", $("#job_requirements").val());
  formData.append("industry", $("#industry").val());
  formData.append("typed_resume", $("#typed_resume").val());

  var file = $("#resume")[0].files[0]; // Get the file from the input field
  if (file) {
    formData.append("resume", file); // Only append the file if one is selected
  }
  // Show the loading spinner
  $("#loading-spinner").show();

  $("input[type='submit']").val("Loading...").prop("disabled", true);

  $.ajax({
    url: "/simulate-interview",
    data: formData,
    type: "POST",
    processData: false,
    contentType: false,
    success: function (response) {
      // Show the loading spinner
      $("#loading-spinner").hide();
      console.log("Response received"); // Add this line
      // Hide the form fields
      $("#interview-form").hide();
      console.log("Form hidden"); // Add this line

      // Store the questions in a global variable
      window.questions = response.interview_questions.filter(function (
        question
      ) {
        // Remove any empty questions
        return question.trim() !== "";
      });

      console.log("Questions array:", window.questions);

      // Display the first question
      $("#question-display").text("1. " + window.questions[0]);
      console.log("First question displayed"); // Add this line

      // Show the navigation buttons
      $("#previous-button, #next-button").show();
      $("#user-answer, #submit-answer").show();
      console.log("Navigation buttons shown"); // Add this line

      // Change the button text back to "Simulate Interview" and enable the button
      $("input[type='submit']")
        .val("Simulate Interview")
        .prop("disabled", false);
    },
    error: function (xhr, textStatus, error) {
      $("#loading-spinner").hide(); // <-- Add this line

      alert("An error occurred. Please try again.");
      $("input[type='submit']")
        .val("Simulate Interview")
        .prop("disabled", false);
    },
  });
});

// ... Remainder of the file ...

$("#submit-answer").on("click", function () {
  // Show the loading spinner
  $("#loading-spinner").show();

  // Get the current question
  var currentQuestion = $("#question-display").text();

  // Get the user's answer
  var userAnswer = $("#user-answer").val();

  // Send an AJAX request to the server with the current question and the user's answer
  $.ajax({
    url: "/analyze-answer",
    data: JSON.stringify({ question: currentQuestion, answer: userAnswer }),
    contentType: "application/json",
    type: "POST",
    success: function (response) {
      // Hide the loading spinner
      $("#loading-spinner").hide();

      // Display the feedback to the user
      alert(response.feedback); // Replace this with the appropriate action
    },
    error: function (xhr, textStatus, error) {
      // Hide the loading spinner
      $("#loading-spinner").hide();

      alert("An error occurred. Please try again.");
    },
  });
});

// When the Next button is clicked...
$("#next-button").on("click", function () {
  // Get the index of the current question
  var index = window.questions.indexOf(
    $("#question-display")
      .text()
      .substring($("#question-display").text().indexOf(" ") + 1)
  );

  // If this isn't the last question, increment the index and display the next question
  if (index < window.questions.length - 1) {
    $("#question-display").text(index + 2 + ". " + window.questions[index + 1]);
  }

  // Clear the user's answer
  $("#user-answer").val("");
});

// When the Previous button is clicked...
$("#previous-button").on("click", function () {
  // Get the index of the current question
  var index = window.questions.indexOf(
    $("#question-display")
      .text()
      .substring($("#question-display").text().indexOf(" ") + 1)
  );

  // If this isn't the first question, decrement the index and display the previous question
  if (index > 0) {
    $("#question-display").text(index + ". " + window.questions[index - 1]);
  }

  // Clear the user's answer
  $("#user-answer").val("");
});

$("#resume").on("change", function () {
  var file = this.files[0];
  if (file) {
    var formData = new FormData();
    formData.append("file", file); // Use 'file' instead of 'resume'

    $.ajax({
      url: "/upload-docx", // Use '/upload-docx' instead of '/upload-resume'
      data: formData,
      type: "POST",
      processData: false,
      contentType: false,
      success: function (response) {
        // Set the content of the typed_resume textarea to the response from the server
        $("#typed_resume").val(response.content); // Use 'response.content' instead of 'response.resume_content'
      },
      error: function (xhr, textStatus, error) {
        alert("An error occurred. Please try again.");
      },
    });
  }
});
