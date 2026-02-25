$(document).ready(function() {
    // Handle the click event for the like button
    $('.likeButton').click(function() {
        var imageId = $(this).data('image-id');
        
        // Send AJAX request to like the image
        $.ajax({
            url: '/like',  // Flask route to handle the like
            method: 'POST',
            data: { imageId: imageId },  // Send image ID to backend
            success: function(response) {
                console.log("something has happened ")
                
                console.log('Updated Likes:', response.newLikes);  // Debugging: check response

                // On success, update the like count on the page
                $('.likeCount[data-image-id="' + imageId + '"]').text('Likes: ' + response.newLikes);
                updateVotingUI(imageId)

            },
            error: function() {
                alert('Error liking the post!');
                console.log("something bad has happened ",imageId)
            }
        });
    });
    // Handle the click event for the dislike button (if applicable)
    $('.disLikeButton').click(function() {
        var imageId = $(this).data('image-id');
        
        // Send AJAX request to dislike the image
        $.ajax({
            url: '/dislike',  // Flask route to handle the dislike
            method: 'POST',
            data: { imageId: imageId },  // Send image ID to backend
            success: function(response) {
                console.log("something has happened ")
                
                console.log('Updated Likes:', response.newLikes);  // Debugging: check response

                // On success, update the like count on the page
                $('.likeCount[data-image-id="' + imageId + '"]').text('Likes: ' + response.newLikes);// replaces the like counter
                updateVotingUI(imageId) // stops teh user from liking the post again
            },
            error: function() {
                alert('Error disliking the post!');
                console.log("something bad has happened ",imageId)
            }
        });
    });
    // this function replaces the like buttons with text that tells teh user that they have already voted for that post.
    function updateVotingUI(imageId) 
    {
        // Find the container of the like/dislike buttons
        const buttonContainer = $(`.likeButton[data-image-id="${imageId}"]`).closest(".flex")
    
        // Replace with "already voted" message
        buttonContainer.replaceWith
        (
          `<div class="flex text-gray-600 mb-2">
                    you have already voted for this post
                </div>`,
        )
    }
});