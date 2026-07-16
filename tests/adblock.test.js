(function(){var p=JSON.parse;JSON.parse=function(){var r=p.apply(this,arguments),c,s;if(r&&typeof r==="object"){delete r.adPlacements;delete r.adSlots;delete r.playerAds;c=r.contents;s=c&&c.sectionListRenderer;if(!s){c=c&&c.tvBrowseRenderer;c=c&&c.content&&c.content.tvSurfaceContentRenderer;s=c&&c.content&&c.content.sectionListRenderer}if(s&&Array.isArray(s.contents))s.contents=s.contents.filter(function(x){return !x.adSlotRenderer&&!x.tvMastheadRenderer})}return r}})();

var player = JSON.parse('{"adPlacements":[1],"adSlots":[2],"playerAds":[3],"videoDetails":{"videoId":"abc"}}');
if ('adPlacements' in player || 'adSlots' in player || 'playerAds' in player) {
  throw new Error('player ads were not removed');
}
if (player.videoDetails.videoId !== 'abc') {
  throw new Error('non-ad player data changed');
}

var home = JSON.parse('{"contents":{"sectionListRenderer":{"contents":[{"adSlotRenderer":{}},{"tvMastheadRenderer":{}},{"shelfRenderer":{"title":"Keep"}}]}}}');
var contents = home.contents.sectionListRenderer.contents;
if (contents.length !== 1 || contents[0].shelfRenderer.title !== 'Keep') {
  throw new Error('home ad filtering failed');
}

'adblock tests passed';
