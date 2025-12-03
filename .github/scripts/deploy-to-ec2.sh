#!/bin/bash
set -e

echo "🚀 Starting deployment to AWS Learner Lab EC2..."

INSTANCE_NAME="smart-notes-app"
REGION="${AWS_REGION:-us-east-1}"
VPC_ID="vpc-02bcc032ca28f08de"
SG_ID="sg-078344c683f54b9d1"

echo "✅ Using VPC: $VPC_ID"
echo "✅ Using Security Group: $SG_ID"

echo "🔒 Attempting to add security group rules..."
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 5000 --cidr 0.0.0.0/0 --region $REGION 2>/dev/null && echo "✅ Port 5000 opened" || echo "⚠️ Port 5000 rule exists"
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $REGION 2>/dev/null && echo "✅ Port 80 opened" || echo "⚠️ Port 80 rule exists"

echo "📦 Finding latest Amazon Linux AMI..."
AMI_ID=$(aws ec2 describe-images --owners amazon --filters "Name=name,Values=al2023-ami-2023.*-x86_64" "Name=state,Values=available" --query 'sort_by(Images, &CreationDate)[-1]. ImageId' --output text --region $REGION)
echo "✅ Using AMI: $AMI_ID"

INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running,pending,stopping,stopped" --query 'Reservations[0].Instances[0].InstanceId' --output text --region $REGION 2>/dev/null || echo "None")

if [ "$INSTANCE_ID" != "None" ] && [ "$INSTANCE_ID" != "" ]; then
    echo "🔄 Found existing instance: $INSTANCE_ID"
    STATE=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0]. State. Name' --output text --region $REGION)
    echo "Current state: $STATE"
    
    if [ "$STATE" == "stopped" ]; then
        echo "▶️ Starting stopped instance..."
        aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION
        aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
    fi
else
    echo "🆕 Creating new EC2 instance..."
    
    cat > /tmp/userdata.sh << 'USERDATA'
#!/bin/bash
exec > /var/log/smart-notes-setup.log 2>&1
echo "Starting Smart Notes EC2 Setup at $(date)"
yum update -y
yum install -y docker git
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user
mkdir -p /home/ec2-user/app
chown -R ec2-user:ec2-user /home/ec2-user/app

cat > /home/ec2-user/deploy-app. sh << 'DEPLOY'
#!/bin/bash
set -e
cd /home/ec2-user/app
if [ -d ". git" ]; then
    git pull
else
    git clone https://github.com/DeltaDixshant/smart-notes. git . 
fi
sudo docker stop smart-notes 2>/dev/null || true
sudo docker rm smart-notes 2>/dev/null || true
sudo docker build -t smart-notes:latest . 
sudo docker run -d -p 5000:5000 --name smart-notes --restart unless-stopped smart-notes:latest
sleep 5
if sudo docker ps | grep smart-notes; then
    PUBLIC_IP=$(curl -s http://169.254. 169.254/latest/meta-data/public-ipv4)
    echo "✅ App deployed at: http://$PUBLIC_IP:5000"
else
    sudo docker logs smart-notes
fi
DEPLOY

chmod +x /home/ec2-user/deploy-app.sh
chown ec2-user:ec2-user /home/ec2-user/deploy-app.sh
echo "Setup complete at $(date)"
USERDATA
    
    INSTANCE_ID=$(aws ec2 run-instances --image-id $AMI_ID --instance-type t2.micro --security-group-ids $SG_ID --user-data file:///tmp/userdata.sh --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" --query 'Instances[0]. InstanceId' --output text --region $REGION)
    
    echo "✅ Instance created: $INSTANCE_ID"
    aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
    sleep 90
fi

PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text --region $REGION)
PUBLIC_DNS=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0]. Instances[0].PublicDnsName' --output text --region $REGION)

echo ""
echo "========================================="
echo "✅ Deployment Information"
echo "========================================="
echo "🆔 Instance ID: $INSTANCE_ID"
echo "🌍 Public IP: $PUBLIC_IP"
echo "🔗 App URL: http://$PUBLIC_IP:5000"
echo "========================================="

if [ -n "$GITHUB_ENV" ]; then
    echo "INSTANCE_ID=$INSTANCE_ID" >> $GITHUB_ENV
    echo "PUBLIC_IP=$PUBLIC_IP" >> $GITHUB_ENV
    echo "APP_URL=http://$PUBLIC_IP:5000" >> $GITHUB_ENV
fi
