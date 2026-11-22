import type { Page } from "@playwright/test";
export async function countMutations(page:Page){
 const counts={posts:0,deletes:0};
 page.on("request",r=>{if(r.method()==="POST")counts.posts++;if(r.method()==="DELETE")counts.deletes++;});
 return counts;
}
