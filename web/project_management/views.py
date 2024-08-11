from http import HTTPStatus
from datetime import datetime
import json

from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.db.models import F, Q
from django.utils import timezone


from user.models import User
from . import models



def try_find_choice(cls, key):
    """Finds a choice from a value, can either be the key or label of a choice

    Parameters
    ----------
        cls : Choice Model
            A TextChoices model
        key : str
            Key to find
    """
    name, label = tuple(zip(*cls.choices))

    if key in name:
        return cls[key].value

    if key in label:
        choices = dict(zip(label, name))
        return cls(choices[key]).value

    return None

@login_required
def kanban(request):
    """
    Creating new project.
    """
    template_name = 'project_management/dashboard.html'
    context = {
        'own_boards': models.Board.objects.filter(owner=request.user),
        'boards': models.Board.objects.filter(members=request.user).filter(~Q(owner=request.user)),
    }
    return render(request, template_name, context)

@login_required
def create_board(request):
    """
    Create new board
    """
    if request.method == 'POST':
        data = request.POST
        try:
            board = models.Board.objects.create(name=data.get('name'), owner=request.user, user_created=request.user, user_updated=request.user)
            board.members.add(board.owner.id)

            if data.get("members") is not None:
                members_data = json.loads(data.get("members"))
                if not isinstance(members_data, list):
                    return JsonResponse({"error": "Members is not type list"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                
                # Get the ids of the members, (pk must exist in property, check frontend)
                members_id = [member["pk"] for member in members_data if "pk" in member]
                board.members.add(*members_id)
            
        except Exception as error:
            return JsonResponse(data={"error": error}, status=HTTPStatus.BAD_REQUEST)

        data = {

        }

        return JsonResponse(data=data, content_type="application/json")
    return JsonResponse({})
    
@login_required
def delete_board(request):
    """
    Delete a board
    """ 
    if request.method == 'POST':
        data = request.POST
        board_id = data.get('id')

        if not board_id:
            return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)

        deleting_board = models.Board.objects.get(id = board_id)
        deleting_board.delete()

        return JsonResponse({}, status=HTTPStatus.OK)
    return JsonResponse({})

@login_required
def update_board(request):
    """
    Update a board

    POST DATA
    ---------
        id: Board id
        name: Updated Name
        members: {
            pk: Member id
        }
    """
    if request.method == 'POST':
        try:
            data = request.POST
            board_id = data.get('id')

            if board_id is None or board_id.strip() == "":
                return JsonResponse({}, status= HTTPStatus.BAD_REQUEST)

            board = models.Board.objects.get(id= board_id)

            updated_name = data.get('name')
            if updated_name != None and updated_name.strip() != "":
                board.name = updated_name

            if data.get("members") is not None:
                members_data = json.loads(data.get("members"))
                if not isinstance(members_data, list):
                    return JsonResponse({"error": "Members is not type list"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                
                # Get the ids of the members, (pk must exist in property, check frontend)
                members_id = [member["pk"] for member in members_data if "pk" in member]

                board.members.clear()
                board.members.add(board.owner.id)
                
                board.members.add(*members_id)

            board.save(user_updated=request.user)

            return JsonResponse({}, status=HTTPStatus.OK)
        except:
            return JsonResponse({"error": "Updating board"}, status=HTTPStatus.BAD_REQUEST)
        
    return JsonResponse({})


@login_required
def search_member(request):
    """Search a member"""

    if request.method != "GET": 
        return JsonResponse({})

    try:
        request_data = request.GET
        query = request_data.get('query')

        print("Searching member " + query)
        search_filter = Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)

        members_list = list(User.objects.exclude(id = request.user.id).filter(search_filter).all()[:10])
        members_data = serializers.serialize('json', members_list)

        data = {
            "members": members_data
        }

        return JsonResponse(data=data, status=HTTPStatus.OK)
    except:
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
    

@login_required
def create_column(request):
    """
    Create column in given board
    """
    if request.method == 'POST':
        try:
            data = request.POST

            if data.get('boardID') is None:
                return JsonResponse({"error": "No board id"}, status=HTTPStatus.BAD_REQUEST)
            
            if data.get('id') is None or data.get('id').strip() == "":
                return JsonResponse({"error": "No column id found"}, status=HTTPStatus.BAD_REQUEST)
            
            if data.get('title') is None or data.get('title').strip() == "":
                return JsonResponse({"error": "No title found"}, status=HTTPStatus.BAD_REQUEST)

            board = models.Board.objects.get(id=data.get('boardID'))

            column = models.Column.objects.create(restID=data.get('id'), title=data.get("title"), board=board)
            column.save(user_updated=request.user)

            data = {

            }

            return JsonResponse(data=data, content_type="application/json", status=HTTPStatus.OK)
        except Exception as e:
            print(e)
            return JsonResponse({"error": f'Unable to create column' }, status=HTTPStatus.BAD_REQUEST)
        
    return JsonResponse({})
    
@login_required
def update_column(request):
    """
    Update column in a given board
    """
    if request.method == 'POST':
        try:
            data = request.POST
            column_id = data.get("id")
            title = data.get("title")
            new_order = data.get("order")

            if column_id is None:
                return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
            
            column = models.Column.objects.get(restID=column_id)

            if title is not None and title.strip() != "":
                column.title = title

            if new_order is not None:
                new_order = int(new_order)
                if column.column_order < new_order:
                    models.Column.objects.filter(board=column.board, column_order__gt=column.column_order, column_order__lte=new_order).update(column_order= F("column_order") - 1)
                else:
                    models.Column.objects.filter(board=column.board, column_order__gte=new_order, column_order__lt=column.column_order).update(column_order= F("column_order") + 1)

                column.column_order = new_order

            column.save(user_updated=request.user)

            return JsonResponse({}, status=HTTPStatus.OK)
        except Exception as e:
            print(e)
            return JsonResponse({"error": "Unable to update column"}, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse({})
                                           

@login_required
def delete_column(request):
    """
    Delete column in given board
    """
    if request.method == 'POST':
        try:
            data = request.POST

            if data.get('id') is None:
                return JsonResponse({"error": "No column id found"}, status=HTTPStatus.BAD_REQUEST)

            column_id = data.get('id')

            # If the id is a string, it's the restID for the column, otherwise it's the id
            if type(column_id) == str:
                column = models.Column.objects.get(restID=column_id)
            else:
                column = models.Column.objects.get(id=column_id)
            
            column.is_valid = 0
            column.save(user_updated=request.user)

            data = {
            }

            return JsonResponse(data=data, content_type="application/json")
        except:
            return JsonResponse({"error": f'Unable to delete column {column_id}'}, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse({})

@login_required
def create_task(request):
    """
    Create card in given column
    """
    if request.method == 'POST':

        try:

            # Split the emails into a list we can use for querying
            assignees = request.POST.get("assignees").split(",")

            # The form data on the website doesn't quite match the fields in the actual model, so
            # we have to build the dict ourselves (another reason why Django Forms are great)
            # two 'id' type fields are passed through, taskID is the restID for the task, while id is the restID
            # for the column (very confusing).
            fields = {
                'restID': request.POST.get('taskID', None),  # The ID for the actual Task
                'title': request.POST.get('title', None),
                'priority': try_find_choice(models.Priority, request.POST.get('priority', None)),
                'description': request.POST.get('description', None),
                'task_order': int(request.POST.get('task_order')),
                'date': request.POST.get("due_date", datetime.today().strftime('%Y-%m-%d')),
                'file': request.FILES.get('file', None),
                'column': models.Column.objects.get(restID=request.POST.get("id", None)),
            }
            if not fields['date']:
                fields['date'] = datetime.today().strftime('%Y-%m-%d')

            # Create the Task object
            task = models.Task.objects.create(**fields, user_created=request.user, user_updated=request.user)
            task.assignees.set(User.objects.filter(email__in=assignees))
            task.save(user_updated=request.user)

            data = {
            }

            return HttpResponse(json.dumps(data), status=200, content_type='application/json')
        except Exception as error:
            print(error)
            return JsonResponse({"error": error}, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse({})

def update_task(request):
    """
    Update given task card
    """
    if request.method == 'POST':
        data = request.POST
        update = {}
        task = models.Task.objects.get(restID=data.get("taskID"))
        update["column"] = task.column

        if data.get("id") != None and data.get("id") != task.column.restID:
            update["column"] = models.Column.objects.get(restID=data.get("id"))

        if data.get("title") != None:
            update["title"] = data.get("title")
        if data.get("priority") != None:
            update["priority"] = try_find_choice(models.Priority, data.get("priority"))
        if data.get("description") != None:
            update["description"] = data.get("description")
        if data.get("task_order") != None:
            update["task_order"] = int(data.get("task_order"))

            updated_column = update["column"]
            if updated_column.restID == task.column.restID:
                if task.task_order < update["task_order"]:
                    models.Task.objects.filter(column=updated_column, task_order__gt=task.task_order, task_order__lte=update["task_order"]).update(task_order = F("task_order") - 1)
                else:
                    models.Task.objects.filter(column=updated_column, task_order__gte=update["task_order"], task_order__lt=task.task_order).update(task_order = F("task_order") + 1)
            else:
                models.Task.objects.filter(column=task.column, task_order__gt=task.task_order).update(task_order = F("task_order") - 1)
                models.Task.objects.filter(column=updated_column, task_order__gte=update["task_order"]).update(task_order = F("task_order") + 1)

        if data.get("due_date") != "" and data.get("due_date") != None:
            update["date"] = datetime.strptime(data.get("due_date"), '%Y-%m-%d')

        models.Task.objects.filter(restID=data.get("taskID")).update( **update)
        task = models.Task.objects.get(restID=data.get("taskID"))
        if data.get("assignees") != None:
            assignees = data.get("assignees").split(",")
            try:
                users = User.objects.filter(email__in=assignees)
            except:
                users= []
            task.assignees.set(users)
        
        if request.FILES.get('file') != None:
            task.file = request.FILES.get('file', None)
        task.save(user_updated=request.user)
        
        data = {
        }

        return JsonResponse(data=data, content_type="application/json")
    return JsonResponse({})

def get_board(request, boardID):
    """
    Get board
    """
    if request.method == "GET":
        board = models.Board.objects.filter(id=boardID).first()
        
        if not board:
            return redirect(reverse('project_management:kanban'))

        try:
            columns = models.Column.objects.filter(board=board,is_valid = 1)
            try:
                serialized_columns = serializers.serialize('json', columns)
            except:
                serialized_columns = serializers.serialize('json', [columns])
        except models.Column.DoesNotExist:
            serialized_columns = []
        try:
            column_ids = set(column.id for column in columns)
            tasks = models.Task.objects.filter(column__in=column_ids).order_by('task_order')
            try:
                serialized_tasks = serializers.serialize('json', tasks)
            except:
                serialized_tasks = serializers.serialize('json', [tasks])
        except models.Task.DoesNotExist:
            serialized_tasks = []

        object_tasks = json.loads(serialized_tasks)

        # Update the 'members' field
        for task_dict in object_tasks:
            print(task_dict)
            assignee_ids = task_dict['fields']['assignees'] 
            assignee_names = [User.objects.get(id=member_id).full_name for member_id in assignee_ids]
            task_dict['fields']['assignees'] = assignee_names

        serialized_tasks = json.dumps(object_tasks)
        

        template_name = 'project_management/board.html'
        context = {
            "board": board,
            "columns": serialized_columns,
            "columnSet": json.loads(serialized_columns),
            "tasks": serialized_tasks,
        }
        return render(request, template_name, context)
    return JsonResponse({})

def get_task(request, restID):
    """
    Get task card
    """
    if request.method == "GET":
        try:
            task = models.Task.objects.get(restID=restID)
 
            serialized_task = serializers.serialize('json', [task], use_natural_foreign_keys=True, use_natural_primary_keys=True)

            deserialized_task = json.loads(serialized_task)

            deserialized_task[0]['fields']['user_updated'] = str(task.user_updated)
            deserialized_task[0]['fields']['date_updated'] = task.date_updated.strftime("%B %d, %Y %I:%M%p")
            

            data = {
                "task": json.dumps(deserialized_task)
            }

            return JsonResponse(data=data, content_type="application/json")
        except Exception as error:
            print(error)
            return JsonResponse({"error": "Unable to get task"}, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse({})
    
@login_required
def delete_task(request):
    if request.method == 'POST':
        try:
            data = request.POST
            task = models.Task.objects.get(restID=data.get("taskID"))

            models.Task.objects.filter(column=task.column, task_order__gt=task.task_order).update(task_order = F("task_order") - 1)
            task.delete(user_updated=request.user)

            return JsonResponse({}, content_type="application/json")
        except:
            return JsonResponse({"error": f'Unable to delete task'}, status=HTTPStatus.BAD_REQUEST)
    
    return JsonResponse({})