const API="http://127.0.0.1:5000/api";

const content=document.getElementById("app-content");

const navItems=[...document.querySelectorAll(".nav-item")];

const state={cache:{},editing:null};



const esc=v=>String(v??"").replace(/&/g,"&amp;").replace(/\</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");

const dateOnly=v=>v?String(v).substring(0,10):"";

const money=v=>"₹"+Number(v||0).toLocaleString("en-IN",{maximumFractionDigits:2});

const fmtDate=v=>{if(!v)return"-";const d=new Date(v);return isNaN(d)?String(v):d.toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"})};

const daysUntil=v=>{if(!v)return Infinity;const a=new Date();a.setHours(0,0,0,0);const b=new Date(v);b.setHours(0,0,0,0);return Math.ceil((b-a)/86400000)};

function toast(msg){
    const box=document.getElementById("toast-container"),
          t=document.createElement("div");

    t.className="toast";
    t.textContent=msg;
    box.appendChild(t);

    setTimeout(()=>t.remove(),2800);
}

async function api(path,opts={}){
    const r=await fetch(API+path,{
        headers:{
            "Content-Type":"application/json",
            ...(opts.headers||{})
        },
        ...opts
    });

    let data={};

    try{
        data=await r.json();
    }catch{}

    if(!r.ok){
        throw new Error(
            data.error||
            data.message||
            `Request failed (${r.status})`
        );
    }

    return data;
}

function setActive(page){
    navItems.forEach(n=>n.classList.toggle("active",n.dataset.page===page));
}

function go(page,push=true){
    setActive(page);

    if(push){
        history.pushState({page},"","#"+page);
    }

    pages[page]?.();
}

navItems.forEach(n=>{
    n.addEventListener("click",()=>go(n.dataset.page));
});

window.addEventListener("popstate",()=>{
    go(location.hash.slice(1)||"dashboard",false);
});

document.getElementById("global-search").addEventListener("input",e=>{
    const q=e.target.value.trim().toLowerCase();

    if(q.length>1){
        showSearch(q);
    }
});

document.getElementById("notification-btn").addEventListener("click",async()=>{
    if(!("Notification" in window)){
        return toast("Browser notifications are not supported.");
    }

    const p=await Notification.requestPermission();

    toast(
        p==="granted"
        ?"Notifications enabled"
        :"Notifications not enabled"
    );
});



function header(eyebrow,title,desc,button=""){
    return `
        <div class="page-header">
            <div>
                <span class="eyebrow">${eyebrow}</span>
                <h1>${title}</h1>
                <p>${desc}</p>
            </div>

            ${
                button
                ?`<button class="primary-button" id="page-action">${button}</button>`
                :""
            }
        </div>
    `;
}

function summary(items){
    return `
        <div class="summary-grid">
            ${
                items.map(x=>`
                    <div class="summary-card">
                        <span>${x[0]}</span>
                        <strong>${x[1]}</strong>
                        ${x[2]?`<small>${x[2]}</small>`:""}
                    </div>
                `).join("")
            }
        </div>
    `;
}

function empty(msg="No records yet."){
    return `<div class="empty">${msg}</div>`;
}



const configs={

    documents:{
        title:"Documents",
        ey:"DOCUMENT VAULT",
        desc:"Track important identity, education, insurance and other documents.",
        path:"documents",
        fields:[
            ["title","Document Title","text",true],
            ["category","Category","select",true,["Identity","Education","Insurance","Vehicle","Travel","Other"]],
            ["document_number","Document Number","text",false],
            ["issue_date","Issue Date","date",false],
            ["expiry_date","Expiry Date","date",false],
            ["notes","Notes","textarea",false]
        ],

        display:(x)=>`${esc(x.title)}|${esc(x.category)}|${x.expiry_date?`Expires ${fmtDate(x.expiry_date)}`:"No expiry"}`
    },



    bills:{
        title:"Bills & Payments",
        ey:"FINANCIAL COMMITMENTS",
        desc:"Track one-time and recurring bills.",
        path:"bills",
        fields:[
            ["name","Bill Name","text",true],
            ["amount","Amount","number",true],
            ["due_date","Due Date","date",true],
            ["category","Category","select",false,["Utilities","Internet","Education","Rent","Insurance","Other"]],
            ["recurring","Recurring","checkbox",false],
            ["frequency","Frequency","select",false,["Weekly","Monthly","Quarterly","Yearly"]],
            ["notes","Notes","textarea",false]
        ],

        display:x=>`${esc(x.name)}|${money(x.amount)}|Due ${fmtDate(x.due_date)}`
    },



    subscriptions:{
        title:"Subscriptions",
        ey:"RECURRING SERVICES",
        desc:"Keep every subscription and renewal date visible.",
        path:"subscriptions",
        fields:[
            ["name","Subscription Name","text",true],
            ["amount","Amount","number",true],
            ["billing_cycle","Billing Cycle","select",true,["Monthly","Quarterly","Yearly"]],
            ["next_billing_date","Next Billing Date","date",true],
            ["category","Category","select",false,["Entertainment","Software","Cloud","Education","Other"]],
            ["status","Status","select",false,["Active","Paused","Cancelled"]],
            ["notes","Notes","textarea",false]
        ],

        display:x=>`${esc(x.name)}|${money(x.amount)}|Next ${fmtDate(x.next_billing_date)}`
    },



    mobile:{
        title:"Mobile & Recharge",
        ey:"MOBILE TRACKER",
        desc:"Track recharge plans, expiry and auto-renewal.",
        path:"mobile-recharges",
        fields:[
            ["mobile_number","Mobile Number","text",true],
            ["operator","Operator","select",true,["Jio","Airtel","Vi","BSNL","Other"]],
            ["plan","Plan","text",true],
            ["amount","Amount","number",true],
            ["recharge_date","Recharge Date","date",true],
            ["expiry_date","Expiry Date","date",true],
            ["frequency","Frequency","select",false,["Weekly","Monthly","Quarterly","Yearly"]],
            ["auto_renew","Auto Renew","checkbox",false],
            ["notes","Notes","textarea",false]
        ],

        display:x=>`${esc(x.operator)} — ${esc(x.plan)}|${esc(x.mobile_number)}|Expires ${fmtDate(x.expiry_date)}`
    },



    warranties:{
        title:"Warranties",
        ey:"PRODUCT PROTECTION",
        desc:"Never lose track of product warranty coverage.",
        path:"warranties",
        fields:[
            ["product","Product","text",true],
            ["purchase_date","Purchase Date","date",true],
            ["expiry_date","Expiry Date","date",true],
            ["provider","Provider","text",false],
            ["serial_number","Serial Number","text",false],
            ["notes","Notes","textarea",false]
        ],

        display:x=>`${esc(x.product)}|${esc(x.provider||"Provider not added")}|Expires ${fmtDate(x.expiry_date)}`
    },



    appointments:{
        title:"Appointments & Important Dates",
        ey:"LIFE CALENDAR",
        desc:"Track appointments, interviews, exams, services and deadlines.",
        path:"appointments",
        fields:[
            ["title","Title","text",true],
            ["date","Date","date",true],
            ["time","Time","time",false],
            ["location","Location","text",false],
            ["category","Category","select",false,["Appointment","Interview","Exam","Travel","Service","Birthday","Deadline","Other"]],
            ["notes","Notes","textarea",false]
        ],

        display:x=>`${esc(x.title)}|${fmtDate(x.date)} ${x.time?esc(x.time):""}|${esc(x.category||"Important date")}`
    }

};



function formHtml(cfg,data=null){

    const f=cfg.fields.map(([key,label,type,req,opts])=>{

        const value=data?.[key]??(type==="checkbox"?false:"");

        if(type==="textarea"){
            return `
                <div class="field full">
                    <label>${label}${req?" *":""}</label>
                    <textarea name="${key}" ${req?"required":""}>${esc(value)}</textarea>
                </div>
            `;
        }

        if(type==="select"){
            return `
                <div class="field">
                    <label>${label}${req?" *":""}</label>

                    <select name="${key}" ${req?"required":""}>
                        <option value="">Select</option>

                        ${
                            opts.map(o=>
                                `<option ${String(value)===o?"selected":""}>${o}</option>`
                            ).join("")
                        }
                    </select>
                </div>
            `;
        }

        if(type==="checkbox"){
            return `
                <div class="field">
                    <label>${label}</label>

                    <label style="display:flex;flex-direction:row;align-items:center;gap:8px;font-weight:400">
                        <input type="checkbox" name="${key}" ${value?"checked":""}>
                        Enable
                    </label>
                </div>
            `;
        }

        return `
            <div class="field">
                <label>${label}${req?" *":""}</label>
                <input name="${key}" type="${type}" value="${esc(value)}" ${req?"required":""}>
            </div>
        `;

    }).join("");

    return `
        <div class="panel form-panel">
            <h3>${data?"Edit":"Add New"} ${cfg.title}</h3>

            <form id="dynamic-form" class="form-grid">

                ${f}

                <div class="field full">
                    <div class="form-actions">
                        <button type="button" class="secondary-button" id="cancel-form">
                            Cancel
                        </button>

                        <button class="primary-button">
                            Save
                        </button>
                    </div>
                </div>

            </form>
        </div>
    `;
}



async function listData(path){
    const d=await api("/"+path);

    state.cache[path]=Array.isArray(d)?d:[];

    return state.cache[path];
}

function statusBadge(date){
    const d=daysUntil(date);

    if(d<0){
        return `<span class="badge danger">OVERDUE</span>`;
    }

    if(d<=30){
        return `<span class="badge warning">SOON</span>`;
    }

    return `<span class="badge success">UPCOMING</span>`;
}

function renderList(cfg,data){

    return data.length

    ?data.map(x=>`
        <div class="item-card">

            <div class="item-top">

                <div>
                    <h4>${cfg.display(x).split("|")[0]}</h4>

                    <p>
                        ${cfg.display(x).split("|").slice(1).join(" · ")}
                    </p>
                </div>

                ${
                    x.expiry_date
                    ?statusBadge(x.expiry_date)
                    :x.due_date
                    ?statusBadge(x.due_date)
                    :x.next_billing_date
                    ?statusBadge(x.next_billing_date)
                    :x.date
                    ?statusBadge(x.date)
                    :""
                }

            </div>

            <div class="meta">
                Created record #${x.id}
            </div>

            <div class="actions">

                <button class="secondary-button edit-record" data-id="${x.id}">
                    Edit
                </button>

                <button class="delete-button delete-record" data-id="${x.id}">
                    Delete
                </button>

            </div>

        </div>
    `).join("")

    :empty();

}



async function modulePage(key){

    const cfg=configs[key];

    content.innerHTML=
        header(
            cfg.ey,
            cfg.title,
            cfg.desc,
            "+ Add "+cfg.title.split(" ")[0]
        )

        +

        `<div id="module-summary"></div>

        <div id="module-body">
            <div class="panel">
                ${empty("Loading...")}
            </div>
        </div>`;

    document.getElementById("page-action").onclick=()=>{
        openForm(key);
    };

    try{

        const data=await listData(cfg.path);

        const relevant=data.filter(x=>{
            const d=
                x.expiry_date||
                x.due_date||
                x.next_billing_date||
                x.date;

            return d&&daysUntil(d)<=30;
        });

        document.getElementById("module-summary").innerHTML=
            summary([
                ["Total",data.length],
                ["Due within 30 days",relevant.length],
                [
                    "Overdue",
                    relevant.filter(x=>
                        daysUntil(
                            x.expiry_date||
                            x.due_date||
                            x.next_billing_date||
                            x.date
                        )<0
                    ).length
                ],
                [
                    "Active / Tracked",
                    data.filter(x=>x.status!=="Cancelled").length
                ]
            ]);

        document.getElementById("module-body").innerHTML=`
            <div class="panel">
                <h3>Records</h3>
                ${renderList(cfg,data)}
            </div>
        `;

        bindList(key);

    }catch(e){

        document.getElementById("module-body").innerHTML=
            `<div class="panel">${empty(e.message)}</div>`;
    }
}



function bindList(key){

    document.querySelectorAll(".edit-record").forEach(b=>{
        b.onclick=()=>editRecord(key,b.dataset.id);
    });

    document.querySelectorAll(".delete-record").forEach(b=>{
        b.onclick=()=>deleteRecord(key,b.dataset.id);
    });
}



async function editRecord(key,id){

    const cfg=configs[key];

    const data=await api(`/${cfg.path}/${id}`);

    openForm(key,data);
}



async function deleteRecord(key,id){

    if(!confirm("Delete this record?"))return;

    const cfg=configs[key];

    await api(`/${cfg.path}/${id}`,{
        method:"DELETE"
    });

    toast("Record deleted");

    modulePage(key);
}



function openForm(key,data=null){

    const cfg=configs[key];

    content.innerHTML=
        header(
            cfg.ey,
            cfg.title,
            data?"Edit record":"New record",
            ""
        )
        +
        formHtml(cfg,data);

    document.getElementById("cancel-form").onclick=()=>{
        modulePage(key);
    };

    document.getElementById("dynamic-form").onsubmit=async e=>{

        e.preventDefault();

        const obj={};

        new FormData(e.target).forEach((v,k)=>{
            obj[k]=v;
        });

        cfg.fields.forEach(([k,,t])=>{
            if(t==="checkbox"){
                obj[k]=e.target.elements[k].checked;
            }
        });

        try{

            await api(
                data
                ?`/${cfg.path}/${data.id}`
                :`/${cfg.path}`,
                {
                    method:data?"PUT":"POST",
                    body:JSON.stringify(obj)
                }
            );

            toast(
                data
                ?"Updated successfully"
                :"Saved successfully"
            );

            modulePage(key);

        }catch(err){

            toast(err.message);
        }
    };
}



function dashboard(){

    content.innerHTML=
        header(
            "OVERVIEW",
            "Dashboard",
            "Your personal digital command center."
        )
        +
        `<div id="dash"></div>`;

    Promise.all(
        Object.values(configs).map(c=>listData(c.path))
    )

    .then(async()=>{

        const all=Object.values(state.cache).flat();

        const upcoming=all.filter(x=>{
            const d=
                x.expiry_date||
                x.due_date||
                x.next_billing_date||
                x.date;

            return d&&daysUntil(d)>=0&&daysUntil(d)<=30;
        });

        const overdue=all.filter(x=>{
            const d=
                x.expiry_date||
                x.due_date||
                x.next_billing_date||
                x.date;

            return d&&daysUntil(d)<0;
        });

        const monthly=all
            .filter(x=>
                x.amount&&
                (
                    x.frequency||
                    x.billing_cycle||
                    ""
                ).toLowerCase().includes("month")
            )
            .reduce((s,x)=>s+Number(x.amount||0),0);

        const sorted=all
            .filter(x=>
                x.expiry_date||
                x.due_date||
                x.next_billing_date||
                x.date
            )
            .sort(
                (a,b)=>
                    new Date(
                        a.expiry_date||
                        a.due_date||
                        a.next_billing_date||
                        a.date
                    )
                    -
                    new Date(
                        b.expiry_date||
                        b.due_date||
                        b.next_billing_date||
                        b.date
                    )
            )
            .slice(0,6);

        document.getElementById("dash").innerHTML=

            summary([
                ["Upcoming 30 Days",upcoming.length],
                ["Overdue",overdue.length],
                ["Monthly Commitments",money(monthly)],
                ["Total Records",all.length]
            ])

            +

            `
            <div class="grid-2">

                <div class="panel">

                    <h3>Needs Attention</h3>

                    ${
                        upcoming
                        .concat(overdue)
                        .slice(0,6)
                        .map(x=>{

                            const d=
                                x.expiry_date||
                                x.due_date||
                                x.next_billing_date||
                                x.date;

                            const title=
                                x.title||
                                x.name||
                                x.product||
                                x.plan||
                                "Item";

                            return `
                                <div class="alert-row">

                                    <div>
                                        <strong style="font-size:12px">
                                            ${esc(title)}
                                        </strong>

                                        <div class="meta">
                                            ${fmtDate(d)}
                                        </div>
                                    </div>

                                    ${statusBadge(d)}

                                </div>
                            `;
                        })
                        .join("")
                        ||
                        empty("Nothing urgent.")
                    }

                </div>


                <div class="panel">

                    <h3>Upcoming Timeline</h3>

                    ${
                        sorted.map(x=>{

                            const d=
                                x.expiry_date||
                                x.due_date||
                                x.next_billing_date||
                                x.date;

                            return `
                                <div class="alert-row">

                                    <div>
                                        <strong style="font-size:12px">
                                            ${esc(
                                                x.title||
                                                x.name||
                                                x.product||
                                                "Item"
                                            )}
                                        </strong>

                                        <div class="meta">
                                            ${fmtDate(d)}
                                        </div>
                                    </div>

                                </div>
                            `;

                        }).join("")
                        ||
                        empty()
                    }

                </div>

            </div>
            `;

    })

    .catch(e=>{
        document.getElementById("dash").innerHTML=
            `<div class="panel">${empty(e.message)}</div>`;
    });
}



async function timeline(){

    content.innerHTML=
        header(
            "CHRONOLOGY",
            "Life Timeline",
            "One chronological view of everything that matters."
        )
        +
        `<div class="panel" id="timeline-panel">
            ${empty("Loading...")}
        </div>`;

    try{

        const rows=[];

        for(const [key,c] of Object.entries(configs)){

            const data=await listData(c.path);

            data.forEach(x=>{

                const d=
                    x.expiry_date||
                    x.due_date||
                    x.next_billing_date||
                    x.date;

                if(d){

                    rows.push({
                        d,
                        title:
                            x.title||
                            x.name||
                            x.product||
                            x.plan,

                        type:c.title,
                        id:x.id
                    });

                }

            });
        }

        rows.sort((a,b)=>new Date(a.d)-new Date(b.d));

        document.getElementById("timeline-panel").innerHTML=

            rows.length

            ?

            `
            <div class="timeline">

                ${
                    rows.map(x=>`
                        <div class="timeline-row">

                            <i class="timeline-dot"></i>

                            <div class="timeline-date">
                                ${fmtDate(x.d)}
                            </div>

                            <div class="timeline-title">
                                ${esc(x.title)}
                            </div>

                            <div class="timeline-type">
                                ${esc(x.type)}
                            </div>

                        </div>
                    `).join("")
                }

            </div>
            `

            :empty();

    }catch(e){

        document.getElementById("timeline-panel").innerHTML=
            empty(e.message);
    }
}



async function analytics(){

    content.innerHTML=
        header(
            "INSIGHTS",
            "Analytics",
            "A simple view of your personal obligations and commitments."
        )
        +
        `<div id="analytics-body">
            ${empty("Loading...")}
        </div>`;

    try{

        const sets=await Promise.all(
            Object.values(configs).map(c=>listData(c.path))
        );

        const names=Object.values(configs).map(c=>c.title);

        const counts=sets.map(x=>x.length);

        const total=counts.reduce((a,b)=>a+b,0);

        const amounts=sets
            .flat()
            .filter(x=>x.amount)
            .reduce((s,x)=>s+Number(x.amount),0);

        document.getElementById("analytics-body").innerHTML=

            summary([
                ["Total Records",total],
                ["Tracked Modules",sets.filter(x=>x.length).length],
                ["Stored Amounts",money(amounts)],
                [
                    "Upcoming",
                    sets.flat().filter(x=>{

                        const d=
                            x.expiry_date||
                            x.due_date||
                            x.next_billing_date||
                            x.date;

                        return d&&daysUntil(d)>=0&&daysUntil(d)<=30;

                    }).length
                ]
            ])

            +

            `
            <div class="panel">

                <h3>Records by Module</h3>

                <div class="stat-list">

                    ${
                        names.map((n,i)=>`

                            <div class="stat-line">

                                <span>${esc(n)}</span>

                                <div class="bar">
                                    <i style="width:${
                                        total
                                        ?Math.max(
                                            3,
                                            counts[i]/total*100
                                        )
                                        :0
                                    }%"></i>
                                </div>

                                <strong>${counts[i]}</strong>

                            </div>

                        `).join("")
                    }

                </div>

            </div>
            `;

    }catch(e){

        document.getElementById("analytics-body").innerHTML=
            empty(e.message);
    }
}



async function assistant(){

    content.innerHTML=
        header(
            "INTELLIGENCE",
            "Life Assistant",
            "Ask about your LifeAdmin data. This version uses your structured data locally through the backend."
        )

        +

        `
        <div class="panel">

            <div class="field">

                <label>Ask a question</label>

                <input
                    id="assistant-q"
                    placeholder="What do I need to take care of this month?"
                >

            </div>

            <div class="form-actions">

                <button class="primary-button" id="ask-ai">
                    Ask Assistant
                </button>

            </div>

        </div>

        <div class="panel">

            <h3>Assistant Response</h3>

            <div
                id="assistant-answer"
                class="assistant-box assistant-answer"
            >
                ${empty("Ask something about your records.")}
            </div>

        </div>
        `;

    document.getElementById("ask-ai").onclick=async()=>{

        const q=
            document.getElementById("assistant-q")
            .value
            .trim();

        if(!q)return;

        document.getElementById("assistant-answer")
            .textContent="Thinking...";

        try{

            const d=
                await api(
                    "/assistant?q="+
                    encodeURIComponent(q)
                );

            document.getElementById("assistant-answer")
                .innerHTML=d.answer;

        }catch(e){

            document.getElementById("assistant-answer")
                .textContent=e.message;
        }
    };
}



/* =========================================================
   SETTINGS
   ========================================================= */

function settings(){

    content.innerHTML=

        header(
            "SYSTEM",
            "Settings",
            "Manage your LifeAdmin preferences, connection and integrations."
        )

        +

        `
        <!-- PROFILE SETTINGS -->

        <div class="panel">

            <div style="
                display:flex;
                align-items:center;
                gap:14px;
                margin-bottom:20px;
            ">

                <div class="user-avatar" style="
                    width:48px;
                    height:48px;
                    font-size:18px;
                ">
                    ${
                        (localStorage.getItem("lifeadmin_name")||"User")
                        .charAt(0)
                        .toUpperCase()
                    }
                </div>

                <div>
                    <h3 style="margin-bottom:4px;">
                        Profile
                    </h3>

                    <p style="
                        margin:0;
                        font-size:12px;
                        color:#667085;
                    ">
                        Personalize your LifeAdmin account.
                    </p>
                </div>

            </div>


            <div class="form-grid">

                <div class="field">

                    <label>Your Name</label>

                    <input
                        id="settings-name"
                        type="text"
                        value="${esc(
                            localStorage.getItem("lifeadmin_name")||"User"
                        )}"
                        placeholder="Enter your name"
                    >

                </div>


                <div class="field">

                    <label>Account Type</label>

                    <input
                        value="Personal Account"
                        disabled
                    >

                </div>

            </div>


            <div class="form-actions">

                <button
                    class="primary-button"
                    id="save-settings"
                >
                    Save Profile
                </button>

            </div>

        </div>



        <!-- BACKEND / API -->

        <div class="panel">

            <div style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                gap:15px;
                margin-bottom:16px;
            ">

                <div>

                    <h3 style="margin-bottom:4px;">
                        Backend & API
                    </h3>

                    <p style="
                        margin:0;
                        font-size:12px;
                        color:#667085;
                    ">
                        Check whether your Flask backend and MySQL database are available.
                    </p>

                </div>

                <span
                    id="api-status-badge"
                    class="badge warning"
                >
                    NOT TESTED
                </span>

            </div>


            <div class="form-grid">

                <div class="field">

                    <label>API Endpoint</label>

                    <input
                        value="${API}"
                        disabled
                    >

                </div>


                <div class="field">

                    <label>Database</label>

                    <input
                        id="database-status"
                        value="Not checked"
                        disabled
                    >

                </div>

            </div>


            <div
                id="api-status-message"
                style="
                    margin-top:12px;
                    font-size:12px;
                    color:#667085;
                "
            >
                Click "Test Connection" to check the backend.
            </div>


            <div class="form-actions">

                <button
                    class="secondary-button"
                    id="test-api"
                >
                    Test Connection
                </button>

            </div>

        </div>



        <!-- CALENDAR -->

        <div class="panel">

            <h3>Calendar Integration</h3>

            <p style="
                font-size:12px;
                color:#667085;
                line-height:1.6;
                margin-top:8px;
            ">

                Download your LifeAdmin dated records as an
                <strong>.ics</strong> calendar file.

                You can import the file into
                Google Calendar, Outlook or Apple Calendar.

            </p>


            <div class="form-actions">

                <button
                    class="secondary-button"
                    id="download-calendar"
                >
                    Download Calendar (.ics)
                </button>

            </div>

        </div>



        <!-- NOTIFICATIONS -->

        <div class="panel">

            <h3>Notifications</h3>

            <p style="
                font-size:12px;
                color:#667085;
                line-height:1.6;
                margin-top:8px;
            ">

                Allow LifeAdmin to show browser notifications
                for important reminders and upcoming records.

            </p>


            <div
                id="notification-status"
                style="
                    margin-top:10px;
                    font-size:12px;
                    font-weight:600;
                "
            >
                Checking notification permission...
            </div>


            <div class="form-actions">

                <button
                    class="secondary-button"
                    id="enable-notifications"
                >
                    Enable Notifications
                </button>

            </div>

        </div>



        <!-- DATA -->

        <div class="panel">

            <h3>Application Data</h3>

            <p style="
                font-size:12px;
                color:#667085;
                line-height:1.6;
                margin-top:8px;
            ">

                LifeAdmin uses your Flask REST API and MySQL
                database for application records.

                Refreshing data reloads the dashboard data from
                the backend.

            </p>


            <div class="form-actions">

                <button
                    class="secondary-button"
                    id="refresh-data"
                >
                    Refresh Application Data
                </button>

                <button
                    class="delete-button"
                    id="clear-preferences"
                >
                    Clear Local Preferences
                </button>

            </div>

        </div>



        <!-- PRIVACY -->

        <div class="panel">

            <h3>Privacy & Security</h3>

            <p style="
                font-size:12px;
                color:#667085;
                line-height:1.7;
                margin-top:8px;
            ">

                LifeAdmin currently stores application records
                in your MySQL database through the local Flask API.

                The current version does not provide production-grade
                authentication or encrypted document storage.

                Do not upload highly sensitive documents until secure
                authentication, authorization and protected file storage
                are implemented.

            </p>

            <div style="
                margin-top:14px;
                padding:12px;
                border-radius:8px;
                background:#f8fafc;
                font-size:12px;
                line-height:1.6;
            ">

                <strong>Current architecture</strong>

                <br>

                Frontend → Flask REST API → MySQL

            </div>

        </div>



        <!-- ABOUT -->

        <div class="panel">

            <h3>About LifeAdmin</h3>

            <p style="
                font-size:12px;
                color:#667085;
                line-height:1.7;
                margin-top:8px;
            ">

                <strong>LifeAdmin</strong> is a personal digital
                command center designed to organize documents,
                bills, subscriptions, mobile recharges, warranties,
                appointments and important dates.

            </p>

            <div style="
                margin-top:12px;
                font-size:11px;
                color:#98A2B3;
            ">

                Personal Digital Command Center · Local Development Version

            </div>

        </div>
        `;



    /* ---------------------------------------------------------
       SAVE PROFILE
       --------------------------------------------------------- */

    document.getElementById("save-settings").onclick=()=>{

        const name=
            document.getElementById("settings-name")
            .value
            .trim()||"User";

        localStorage.setItem(
            "lifeadmin_name",
            name
        );

        document.getElementById("user-name")
            .textContent=name;

        const avatar=document.querySelector(".user-avatar");

        if(avatar){
            avatar.textContent=
                name.charAt(0).toUpperCase();
        }

        toast("Profile saved successfully");
    };



    /* ---------------------------------------------------------
       TEST BACKEND CONNECTION
       --------------------------------------------------------- */

    document.getElementById("test-api").onclick=async()=>{

        const button=
            document.getElementById("test-api");

        const badge=
            document.getElementById("api-status-badge");

        const message=
            document.getElementById("api-status-message");

        const database=
            document.getElementById("database-status");


        button.disabled=true;
        button.textContent="Testing...";

        badge.className="badge warning";
        badge.textContent="TESTING";

        message.textContent=
            "Connecting to Flask backend...";


        try{

            const result=
                await api("/health");


            badge.className="badge success";
            badge.textContent="CONNECTED";

            database.value=
                result.database||
                "Connected";


            message.textContent=
                result.message||
                "LifeAdmin API is healthy.";

            toast("Backend connection successful");

        }catch(e){

            badge.className="badge danger";
            badge.textContent="OFFLINE";

            database.value="Unavailable";

            message.textContent=
                "Unable to connect to the LifeAdmin backend. Make sure Flask is running on http://127.0.0.1:5000.";

            toast("Backend connection failed");

        }finally{

            button.disabled=false;
            button.textContent="Test Connection";
        }

    };



    /* ---------------------------------------------------------
       CALENDAR DOWNLOAD
       --------------------------------------------------------- */

    document.getElementById("download-calendar").onclick=async()=>{

        try{

            const r=
                await fetch(API+"/calendar.ics");

            if(!r.ok){
                throw new Error(
                    `Calendar request failed (${r.status})`
                );
            }

            const blob=
                await r.blob();

            const url=
                URL.createObjectURL(blob);

            const a=
                document.createElement("a");

            a.href=url;
            a.download="lifeadmin-calendar.ics";

            document.body.appendChild(a);

            a.click();

            a.remove();

            URL.revokeObjectURL(url);

            toast("Calendar downloaded");

        }catch(e){

            toast(e.message);
        }

    };



    /* ---------------------------------------------------------
       NOTIFICATIONS
       --------------------------------------------------------- */

    const notificationStatus=
        document.getElementById("notification-status");

    const notificationButton=
        document.getElementById("enable-notifications");


    if(!("Notification" in window)){

        notificationStatus.textContent=
            "Browser notifications are not supported.";

        notificationButton.disabled=true;

    }else{

        const permission=
            Notification.permission;

        if(permission==="granted"){

            notificationStatus.textContent=
                "Notifications are enabled.";

        }else if(permission==="denied"){

            notificationStatus.textContent=
                "Notifications are blocked in your browser.";

        }else{

            notificationStatus.textContent=
                "Notifications have not been enabled yet.";
        }

    }


    notificationButton.onclick=async()=>{

        if(!("Notification" in window)){
            return toast(
                "Browser notifications are not supported."
            );
        }

        const permission=
            await Notification.requestPermission();

        if(permission==="granted"){

            notificationStatus.textContent=
                "Notifications are enabled.";

            toast("Notifications enabled");

        }else if(permission==="denied"){

            notificationStatus.textContent=
                "Notifications are blocked in your browser.";

            toast("Notifications blocked");

        }else{

            notificationStatus.textContent=
                "Notification permission was not granted.";

            toast("Notifications not enabled");
        }

    };



    /* ---------------------------------------------------------
       REFRESH APPLICATION DATA
       --------------------------------------------------------- */

    document.getElementById("refresh-data").onclick=async()=>{

        const button=
            document.getElementById("refresh-data");

        button.disabled=true;
        button.textContent="Refreshing...";

        try{

            state.cache={};

            for(const cfg of Object.values(configs)){
                await listData(cfg.path);
            }

            toast("Application data refreshed");

        }catch(e){

            toast(
                "Refresh failed: "+e.message
            );

        }finally{

            button.disabled=false;
            button.textContent=
                "Refresh Application Data";
        }

    };



    /* ---------------------------------------------------------
       CLEAR LOCAL PREFERENCES
       --------------------------------------------------------- */

    document.getElementById("clear-preferences").onclick=()=>{

        const confirmed=
            confirm(
                "Clear your saved local LifeAdmin preferences? This will remove your saved name from this browser. Your MySQL records will NOT be deleted."
            );

        if(!confirmed)return;

        localStorage.removeItem(
            "lifeadmin_name"
        );

        document.getElementById("settings-name")
            .value="User";

        document.getElementById("user-name")
            .textContent="User";

        const avatar=
            document.querySelector(".user-avatar");

        if(avatar){
            avatar.textContent="U";
        }

        toast("Local preferences cleared");
    };

}



async function showSearch(q){

    content.innerHTML=
        header(
            "SEARCH",
            "Search Results",
            `Searching for “${esc(q)}”`
        )
        +

        `<div class="panel search-results" id="search-results">
            ${empty("Searching...")}
        </div>`;

    try{

        const d=
            await api(
                "/search?q="+
                encodeURIComponent(q)
            );

        document.getElementById("search-results").innerHTML=

            d.results.length

            ?

            d.results.map(x=>`
                <div class="alert-row">

                    <div>

                        <strong style="font-size:12px">
                            ${esc(x.title)}
                        </strong>

                        <div class="meta">
                            ${esc(x.type)} · ${esc(x.detail)}
                        </div>

                    </div>

                </div>
            `).join("")

            :empty("No matching records.");

    }catch(e){

        document.getElementById("search-results").innerHTML=
            empty(e.message);
    }

}



const pages={
    dashboard,
    timeline,
    analytics,
    assistant,
    settings,

    documents:()=>modulePage("documents"),
    bills:()=>modulePage("bills"),
    subscriptions:()=>modulePage("subscriptions"),
    mobile:()=>modulePage("mobile"),
    warranties:()=>modulePage("warranties"),
    appointments:()=>modulePage("appointments")
};



document.getElementById("user-name").textContent=
    localStorage.getItem("lifeadmin_name")||"User";



go(
    location.hash.slice(1)||"dashboard",
    false
);