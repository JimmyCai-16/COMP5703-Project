from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from file.models import File
from file.serializers import FileSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status,views
from main.permissions import IsAuthenticated

class UploadFiles(ModelViewSet):
    permission_classes=[IsAuthenticated,]
    queryset = File.objects.all()
    serializer_class = FileSerializer

    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        files = request.data.getlist('file')
        names = request.data.getlist('name')
        try:
            serializer = self.serializer_class(data=request.data,  many=True)
            
            valid = serializer.is_valid(raise_exception=True)
            if(valid):
                instances = []
                i=0                
                for file in files:
                    instance = File(file=file, name=names[i])
                    instances.append(instance)
                    i = i+1
                created_files = File.objects.bulk_create(instances)
                serializer = FileSerializer(created_files, many=True)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print("File create error", e)
            
class DeleteFiles(views.APIView):
    permission_classes=[IsAuthenticated,]

    serializer_class = FileSerializer
    def post(self, request):
        file_ids = request.data.get('file_ids', [])  # Assuming the frontend sends an array of file IDs
        files = File.objects.filter(id__in=file_ids)

        # Check if all the files exist
        if len(files) != len(file_ids):
            return Response({'error': 'One or more files do not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Delete the files
        files.delete()

        return Response({'message': 'Files deleted successfully'}, status=status.HTTP_200_OK)    