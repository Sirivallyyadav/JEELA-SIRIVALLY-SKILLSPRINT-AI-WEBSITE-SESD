document.addEventListener("DOMContentLoaded",()=>{
 const qs=document.getElementById("questionSelect"), qt=document.getElementById("questionText");
 if(qs&&qt) qs.addEventListener("change",()=>qt.textContent=qs.value);
 const start=document.getElementById("startSpeech"), stop=document.getElementById("stopSpeech");
 if(start){
   const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
   const status=document.getElementById("speechStatus"), transcript=document.getElementById("transcript");
   let rec=null;
   if(!SR){start.addEventListener("click",()=>status.textContent="Speech recognition is not supported in this browser. Try a current version of Chrome or type your answer.");}
   else{
     rec=new SR(); rec.lang="en-IN"; rec.continuous=true; rec.interimResults=true;
     rec.onstart=()=>status.textContent="Listening… speak clearly.";
     rec.onerror=e=>status.textContent="Microphone issue: "+e.error+". Check browser permission.";
     rec.onend=()=>status.textContent="Listening stopped.";
     rec.onresult=e=>{let finalText=""; for(let i=e.resultIndex;i<e.results.length;i++){if(e.results[i].isFinal) finalText+=e.results[i][0].transcript+" ";} transcript.value=(transcript.value+" "+finalText).trim();};
     start.addEventListener("click",()=>{try{rec.start()}catch(e){status.textContent="Already listening. Press Stop first."; }});
     stop.addEventListener("click",()=>rec.stop());
   }
 }
 const wc=document.getElementById("wordCount");
 if(wc) wc.addEventListener("click",()=>{const n=(document.getElementById("transcript").value.trim().match(/\S+/g)||[]).length;document.getElementById("wordResult").textContent=n+" words · "+(n<60?"Try adding a specific example.":n>180?"Consider making the answer more concise.":"Good practice length.");});
 const form=document.getElementById("chatForm");
 if(form) form.addEventListener("submit",async e=>{
   e.preventDefault(); const input=document.getElementById("chatInput"), box=document.getElementById("chatMessages"), msg=input.value.trim(); if(!msg)return;
   const add=(text,cls)=>{const d=document.createElement("div");d.className="bubble "+cls;d.textContent=text;box.appendChild(d);box.scrollTop=box.scrollHeight;};
   add(msg,"user");input.value="";
   try{const r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg})});const data=await r.json();add(data.reply,"bot");}
   catch(err){add("I couldn't reach the server. Please try again.","bot");}
 });
});
