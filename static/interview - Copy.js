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

    if (xhr.status === 403) {
      // Handle the specific case of a 403 error
      alert("Access Denied. This feature is available for Premium Plus Plan subscribers only.");
    } else {
      // Handle other errors
      alert("An error occurred. Please try again.");
    }
      $("input[type='submit']")
        .val("Simulate Interview")
        .prop("disabled", false);
    },
  });
});

// Code for handling answer submission
$("#submit-answer").on("click", function () {
  // Show the loading spinner
  $("#loading-spinner").show();

  // Get the current question
  var currentQuestion = $("#question-display").text();

  // Get the user's answer
  var userAnswer = $("#user-answer").val();

  // AJAX call to analyze the answer
  $.ajax({
    url: "/analyze-answer",
    data: JSON.stringify({ question: currentQuestion, answer: userAnswer }),
    contentType: "application/json",
    type: "POST",
    success: function (response) {
      // Hide the loading spinner
      $("#loading-spinner").hide();
      // Insert the feedback into the modal's body
      $("#modal-body-content").html(response.feedback);
      // Show the modal
      $("#feedbackModal").modal("show");
    },
    error: function (xhr, textStatus, error) {
      // Hide the loading spinner
      $("#loading-spinner").hide();
      // Display an error message in the modal
      $("#modal-body-content").html("An error occurred. Please try again.");
      // Show the modal
      $("#feedbackModal").modal("show");
    }
  });
});  // This closing bracket and parenthesis were added to close the click event handler

// Code for handling the Next button
$("#next-button").on("click", function () {
  var index = window.questions.indexOf(
    $("#question-display")
      .text()
      .substring($("#question-display").text().indexOf(" ") + 1)
  );
  if (index < window.questions.length - 1) {
    $("#question-display").text(index + 2 + ". " + window.questions[index + 1]);
  }
  $("#user-answer").val("");
});

// Code for handling the Previous button
$("#previous-button").on("click", function () {
  var index = window.questions.indexOf(
    $("#question-display")
      .text()
      .substring($("#question-display").text().indexOf(" ") + 1)
  );
  if (index > 0) {
    $("#question-display").text(index + ". " + window.questions[index - 1]);
  }
  $("#user-answer").val("");
});

// Code for handling resume upload
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
        $("#typed_resume").val(response.content); // Use 'response.content' instead of 'response.resume_content'
      },
      error: function (xhr, textStatus, error) {
        alert("An error occurred. Please try again.");
      }
    });
  }
});
