var width = 320;
var height = 0;
var streaming = false;
var video = null;
var canvas = null;
var photo = null;
var startbutton = null;
var imageDataInput = null;
var mediaStream = null;

function initializeCamera() {
  video = document.getElementById('video');
  canvas = document.getElementById('canvas');
  photo = document.getElementById('photo');
  startbutton = document.getElementById('startbutton');
  imageDataInput = document.getElementById('image-data');
  if (!video || !canvas || !photo || !startbutton || !imageDataInput) {
    // console.error("One or more required HTML elements are missing.");
    return;
  }

  navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    .then(function(stream) {
      mediaStream = stream;
      video.srcObject = stream;
      video.play();
    })
    .catch(function(err) {
      console.log("An error occurred: " + err);
    });

  video.addEventListener('canplay', function(ev){
    if (!streaming) {
      height = video.videoHeight / (video.videoWidth/width);
      if (isNaN(height)) {
        height = width / (4/3);
      }
      video.setAttribute('width', width);
      video.setAttribute('height', height);
      canvas.setAttribute('width', width);
      canvas.setAttribute('height', height);
      streaming = true;
    }
  }, false);

  startbutton.addEventListener('click', function(ev){
    takepicture();
    ev.preventDefault();
  }, false);

  clearphoto();
}

function clearphoto() {
  var context = canvas.getContext('2d');
  context.fillStyle = "#AAA";
  context.fillRect(0, 0, canvas.width, canvas.height);

  var data = canvas.toDataURL('image/png');
  photo.setAttribute('src', data);
  imageDataInput.value = data;
}

function takepicture() {
  var context = canvas.getContext('2d');
  if (width && height) {
    canvas.width = width;
    canvas.height = height;
    context.drawImage(video, 0, 0, width, height);

    var data = canvas.toDataURL('image/png');
    photo.setAttribute('src', data);
    imageDataInput.value = data;
  } else {
    clearphoto();
  }
}

function startup() {
  // Initialize camera and other stuff
  initializeCamera();
}
// Function to stop the camera stream and release resources
function stopCamera() {
  if (mediaStream) {
    const tracks = mediaStream.getTracks();
    tracks.forEach(track => track.stop());
    mediaStream = null; // Reset mediaStream variable after stopping the stream
  }
}


// On initial page load and htmx load
// window.addEventListener('load', startup, false);
document.addEventListener('htmx:load', startup);
// On htmx page transition
document.addEventListener('htmx:afterSwap', stopCamera);
// window.addEventListener('beforeunload', stopCamera);