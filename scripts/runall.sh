# servers=(og eun1a euw1b sae1a use2a usnyc1 usw1a)
servers=(og eun1a euw1b sae1a use2a usw1a)
for i in "${servers[@]}"; 
do 
	ssh -t $i "vnstat -5 100 > "  
done


