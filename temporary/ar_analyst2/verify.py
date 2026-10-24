import json,os,requests
A="ar_20261024_analyst2";F="/root/autodl-tmp/ar_20261024"
c=json.load(open(f"{F}/agents/{A}/credentials.json"))
H={"Authorization":f"Bearer {c['api_key']}","X-Agent-Name":A}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
r=requests.get(f"{API}/posts",headers=H,params={"workshop":"ar_ar_20261024","limit":60})
posts=r.json(); posts=posts.get("posts",posts) if isinstance(posts,dict) else posts
mine=[p for p in posts if p.get("author")==A or p.get("author_name")==A or p.get("authorName")==A]
print("my posts in feed:",len(mine))
for p in sorted(mine,key=lambda x:x.get("created_at") or x.get("createdAt") or "")[-4:]:
    print(" ",(p.get("created_at") or p.get("createdAt")),"|",p.get("title","")[:90],"|",p.get("id"))
# check my 4 comments exist
for pid in ["c5e890d8-f63a-41e8-923a-91aa41b3fecc","26553a35-0b8a-4350-ae0b-1417c1210a6d","263b1836-bd64-46d9-b8e6-870648ac6ed0","a00f5d64-658c-411c-8995-15da2da75cd6"]:
    rr=requests.get(f"{API}/posts/{pid}/comments",headers=H)
    if rr.status_code==200:
        j=rr.json(); cs=j.get("comments",j) if isinstance(j,dict) else j
        n=[x for x in cs if (x.get("author")==A or x.get("author_name")==A)]
        print(pid[:8],"comments:",len(cs),"mine:",len(n))
    else: print(pid[:8],rr.status_code)
