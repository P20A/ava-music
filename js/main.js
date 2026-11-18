const root=document.documentElement;
const themeBtn=document.getElementById("themeBtn");
const saved=localStorage.getItem("ava-theme");
if(saved) root.dataset.theme=saved;
function labelTheme(){themeBtn.innerHTML=root.dataset.theme==="dark"?"☼ <span>حالت روشن</span>":"☾ <span>حالت تیره</span>"}
labelTheme();
themeBtn.addEventListener("click",()=>{root.dataset.theme=root.dataset.theme==="dark"?"light":"dark";localStorage.setItem("ava-theme",root.dataset.theme);labelTheme()});

const menuBtn=document.getElementById("menuBtn"),nav=document.getElementById("navLinks");
menuBtn.addEventListener("click",()=>{const open=nav.classList.toggle("open");menuBtn.setAttribute("aria-expanded",String(open))});
nav.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>{nav.classList.remove("open");menuBtn.setAttribute("aria-expanded","false")}));

const searchForm=document.getElementById("searchForm"),search=document.getElementById("search");
searchForm.addEventListener("submit",e=>e.preventDefault());
search.addEventListener("input",()=>{const q=search.value.trim().toLowerCase();document.querySelectorAll(".music-post").forEach(post=>{post.hidden=!post.innerText.toLowerCase().includes(q)})});

const dock=document.getElementById("audioDock"),play=document.getElementById("playPause");
document.querySelectorAll(".cover-play").forEach(btn=>btn.addEventListener("click",e=>{e.preventDefault();const post=btn.closest(".music-post");document.getElementById("dockTitle").textContent=post.querySelector("h3").innerText;document.getElementById("dockArtist").textContent=post.querySelector(".post-bottom b").innerText;dock.style.display="grid";play.textContent="Ⅱ"}));
play.addEventListener("click",()=>play.textContent=play.textContent==="▶"?"Ⅱ":"▶");
document.getElementById("closeDock").addEventListener("click",()=>dock.style.display="none");
