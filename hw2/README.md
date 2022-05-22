#instructions:  
##1.Make sure you are at the same directory as the deploy.sh file.  
##2.Make sure you have your AWS cli configures and has the needed permission to run these operations -   
 - create cloud formation.
 - create ssh key.

##3.Create dummy binary file to test the env.
 - ```head -c 100000 /dev/urandom >dummy```

##4.Run the deploy.sh file, it will output all the operations it preformed.
 
##5.Test your code with both endpoints - 
```curl "http://<one of the ec2's public ips>:5000/enqueue?iterations=3" -F "data=@path/to/dummy/file" -X PUT```  
```curl -X POST "http://<one of the ec2's public ips>:5000/pullCompleted?top=<number of jobs you want>"```  


#How to handle fails -  
###1.one of Node fails:  
In this case, the system will continue to work as expected, the only thing is that the the specific node  
that failed will not answer the API calls, If it was a real world situation i would create a load balancer  
that will handle the state of the machines (Target group in AWS case), this way i provide the user a single api  
DNS record, and he don't need to think about "if the node is up or not".  
###2.The redis DB will fail / network split.  
In this case, the system will not work anymore, if it was a real world situation, I would create a redis cluster (self maintained oe SAAS solution)  
With a redis cluster i can be fault tolerant to any node failures, because I can provide HA to the redis queues.  
If we have network fail we will use the leader election mechanism if redis cluster and will continue to serve the right finished jobs.
###3.CPU\Mem limit reach -  
In this case we will probably get some timeouts from the API, in real world situation i would have created  
an aws ASG with cloud watch metrics that check if the cpu or memory is above a certain threshold, if so it would scale the group,  
this way the ASG can now handle all the load and scale down if needed.  

##Architecture diagram
![Alt text](architecture_of_the_solution.png?raw=true "Title")

