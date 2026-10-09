import re

def parse(s):
 stack=[];root=None
 for t in re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]',s):
  if t=='(':
   a=[]
   if stack:stack[-1].append(a)
   else:root=a
   stack.append(a)
  elif t==')':stack.pop()
  else:stack[-1].append(t)
 assert not stack
 return root

def children(a,k):return [x for x in a if isinstance(x,list) and x[0]==k]
def child(a,k):return next(iter(children(a,k)))
def dump(a,depth=0):
 if not isinstance(a,list):return a
 if not any(isinstance(x,list) for x in a):return '('+' '.join(a)+')'
 lead=[];tail=[]
 for x in a:(tail if isinstance(x,list) else lead).append(x)
 return '('+' '.join(lead)+'\n'+'\n'.join('\t'*(depth+1)+dump(x,depth+1) for x in tail)+'\n'+'\t'*depth+')'
