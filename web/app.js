let articles = [];
let activeFilter = "All";
const platforms = {
  OpenAI: /openai|chatgpt|sora/i, Anthropic: /anthropic|claude/i,
  Google: /google|gemini|deepmind/i, Microsoft: /microsoft|copilot/i,
  Meta: /meta ai|llama/i
};
const esc = value => String(value || "").replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
function platformFor(article){const text=`${article.title} ${article.source}`;return Object.keys(platforms).find(key=>platforms[key].test(text))||"Other"}
function dateLabel(value){if(!value)return "Time unavailable";return new Intl.DateTimeFormat("en",{month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"}).format(new Date(value))}
function render(){
  const filtered=articles.filter(a=>activeFilter==="All"||platformFor(a)===activeFilter);
  const lead=document.querySelector("#lead-story"), grid=document.querySelector("#news-grid"), empty=document.querySelector("#empty-state");
  empty.hidden=filtered.length>0; lead.hidden=!filtered.length; lead.classList.remove("skeleton");
  if(filtered.length){const a=filtered[0];lead.innerHTML=`<span class="kicker">${esc(platformFor(a))} / Lead signal</span><a href="${esc(a.url)}" target="_blank" rel="noopener"><h3>${esc(a.title)}</h3></a><span class="meta">${esc(a.source)} · ${dateLabel(a.published)}</span>`}
  grid.innerHTML=filtered.slice(1).map(a=>`<article class="card"><span class="kicker">${esc(platformFor(a))} / ${esc(a.topic)}</span><a href="${esc(a.url)}" target="_blank" rel="noopener"><h3>${esc(a.title)}</h3></a><p>${esc(a.snippet||"Open the source for the complete story and context.")}</p><span class="meta">${esc(a.source)} · ${dateLabel(a.published)}</span></article>`).join("");
}
async function loadNews(){
  document.querySelector("#update-label").textContent="Updating live intelligence…";
  try{const response=await fetch("/api/news");const data=await response.json();if(!response.ok)throw new Error(data.error||"Feed unavailable");articles=data.articles||[];
    document.querySelector("#story-count").textContent=articles.length;document.querySelector("#source-count").textContent=new Set(articles.map(a=>a.source)).size;
    document.querySelector("#update-label").textContent=`Updated ${dateLabel(data.updated_at)} · ${data.lookback_hours}h window`;render();
  }catch(error){document.querySelector("#lead-story").classList.remove("skeleton");document.querySelector("#lead-story").innerHTML=`<span class="kicker">Connection notice</span><h3>LIVE FEED TEMPORARILY UNAVAILABLE.</h3><span class="meta">${esc(error.message)}</span>`;document.querySelector("#update-label").textContent="Could not update"}
}
document.querySelectorAll(".filters button").forEach(button=>button.addEventListener("click",()=>{document.querySelector(".filters .active").classList.remove("active");button.classList.add("active");activeFilter=button.dataset.filter;render()}));
document.querySelectorAll(".refresh").forEach(button=>button.addEventListener("click",loadNews));
loadNews();
