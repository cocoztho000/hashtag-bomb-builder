// CRUD operations on favorite tags


function AddFavoriteTag(favoriteSearchTagName, tagResults) {
  if (favoriteSearchTagName === undefined || favoriteSearchTagName === "" || tagResults === undefined || tagResults == ""){
    console.log("Search Feild is empty, setting start as grey");
    setStarGrey();
    return
  }

  var favoritesCookie = getFavoriteTag();

  if (ExistsFavoriteTag(favoriteSearchTagName)){
    updateFavoiteTag(favoriteSearchTagName, tagResults);
  } else {
    console.log(tagResults);
    var newTag = {
      "tagName": favoriteSearchTagName,
      "tagDataStr": tagResults,
    };
    favoritesCookie.push(newTag);
    setFavoriteTag(favoritesCookie);
  }
}

function ExistsFavoriteTag(favoriteTag){
  var favoritesCookie = getFavoriteTag();

  for (var i = 0; i < favoritesCookie.length; i++) {
    if (favoritesCookie[i].tagName == favoriteTag) {
      return true;
    }
  }
  return false;
}

function DeleteFavoriteTag(favoriteTagToDelete) {
    var favoritesCookie = getFavoriteTag();
  
    var newCookie = [];
    for (var i = 0; i < favoritesCookie.length; i++) {
      if (favoritesCookie[i].tagName != favoriteTagToDelete) {
        newCookie.push(favoritesCookie[i]);
      }
    }
    setFavoriteTag(newCookie);
  }
  

function updateFavoiteTag(favoriteSearchTagName, tagResults){
  var favoritesCookie = getFavoriteTag();

  for (var i = 0; i < favoritesCookie.length; i++) {
    if (favoritesCookie[i].tagName == favoriteSearchTagName) {
      favoritesCookie[i].tagDataStr = tagResults; 
    }
  }
  setFavoriteTag(favoritesCookie);
}

function setFavoriteTag(newTagCookieToSet) {
  Cookies.set(FAVORITES_COOKIE, newTagCookieToSet)
}

function getFavoriteTag(){
  var result = [];
  var favoritesCookieData = Cookies.getJSON(FAVORITES_COOKIE);

  if (favoritesCookieData === undefined){
    return result;
  }

  for(var i in favoritesCookieData) {
    result.push(favoritesCookieData[i]);
  }
  return result;
}
