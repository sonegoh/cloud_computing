#instructions:
#1.Make sure you are at the same directory as the deploy.sh file.
#2.Make sure you have your AWS cli configures and has the needed permission to run these operations - 
 - create cloud formation.
 - create ssh key.

#3.Create dummy binary file to test the env.
 - ```head -c 100000 /dev/urandom >dummy```
#4.Run the deploy.sh file, it will output all the operations it preformed.
 
#5.Test your code with both endpoints - 
```curl "http://<one of the ec2's public ips>:5000/enqueue?iterations=3" -F "data=@path/to/dummy/file" -X PUT```
```curl -X POST "http://<one of the ec2's public ips>:5000/pullCompleted?top=<number of jobs you want>"```

#Note - Architecture diagram
Check the architecture_of_the_solution.png , it contains an image of the stack architecture